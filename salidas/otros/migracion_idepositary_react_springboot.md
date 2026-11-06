# Plan de Migración: iDepositary (Java EE + JSF) → React + Spring Boot
**Sistema:** iDepositary — Core de Mercado de Capitales (Pradera)  
**Fecha:** 2026-04-28  
**Versión:** 1.0  

---

## 1. Diagnóstico del Sistema Actual

### Inventario de módulos

| Módulo | Tipo | Líneas Java aprox. | Tecnología clave |
|---|---|---|---|
| `iIntegration` | JAR | ~40 archivos | Interfaces, contratos, tipos base, Validaciones, JWT |
| `iModel` | JAR | ~300 entidades | JPA/Hibernate 5.3, dominio completo |
| `iCoreFramework` | JAR | ~30 archivos | EJB Batch propio, Audit Interceptor |
| `iCommons` | JAR | ~200 archivos | PrimeFaces 6.2, OmniFaces, DeltaSpike, SFTP, Jasper |
| `iCoreComponent` | JAR | ~400 archivos | SOAP/Axis 1.4, QR, PDFBox, servicios BC |
| `iAccounts` | WAR | ~1400 archivos | JSF MgmtBeans, Facades, Services, DAOs, Batch, HubSpot |

**Total: 2.295 archivos Java + 331 páginas XHTML**

### Stack tecnológico actual

```
┌─────────────────────────────────────────────────────────┐
│             CLIENTE (Navegador)                          │
│  PrimeFaces 6.2 + XHTML/Facelets + OmniFaces            │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTP / JSF Lifecycle
┌─────────────────────▼───────────────────────────────────┐
│            WildFly / JBoss (Java EE 8)                  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  View Layer — JSF MgmtBeans (@Named, ViewScoped)   │ │
│  │  HolderMgmtBean, AssetLaundryBean, HolderAcct...   │ │
│  └───────────────────┬────────────────────────────────┘ │
│                      │ @EJB injection                    │
│  ┌───────────────────▼────────────────────────────────┐ │
│  │  Facade Layer — EJB @Stateless                     │ │
│  │  HolderServiceFacade, AssetLaundryFacade...        │ │
│  └───────────────────┬────────────────────────────────┘ │
│                      │ @EJB / @Inject                   │
│  ┌───────────────────▼────────────────────────────────┐ │
│  │  Service Layer — EJB @Stateless ServiceBeans       │ │
│  │  HolderServiceBean, BatchServiceBean...            │ │
│  └───────────────────┬────────────────────────────────┘ │
│                      │ JPA/Hibernate                     │
│  ┌───────────────────▼────────────────────────────────┐ │
│  │  DAO Layer — EJB extends CrudDaoServiceBean        │ │
│  │  HolderAccountDAO, AccountStatementDAO...          │ │
│  └───────────────────┬────────────────────────────────┘ │
│                      │                                   │
│  ┌───────────────────▼────────────────────────────────┐ │
│  │  iModel — JPA Entities (javax.persistence.*)       │ │
│  │  Holder, HolderAccount, OperationSettlement...     │ │
│  └───────────────────┬────────────────────────────────┘ │
│                      │                                   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Cross-cutting                                   │   │
│  │  iIntegration │ iCoreFramework │ iCommons        │   │
│  │  JWT │ Audit │ Batch │ SFTP │ JasperReports      │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  External: SOAP/Axis (BCB, EDV) │ REST (HubSpot)        │
└─────────────────────────────────────────────────────────┘
            │                         │
       Oracle/PostgreSQL         File System
```

### Dominio del negocio (iModel)

El modelo de dominio cubre:

| Subdominio | Entidades clave |
|---|---|
| **Cuentas** | `Holder`, `HolderAccount`, `HolderAccountDetail`, `Participant`, `CashAccount` |
| **Liquidación** | `OperationSettlement`, `SettlementProcess`, `TradeSettlementRequest`, `ParticipantPenalty` |
| **Contabilidad** | `AccountingProcess`, `AccountingAccount`, `AccountingMatrix`, `AccountingReceipt` |
| **PLAFT/AML** | `UIF`, `OFAC`, `PEP`, `PNA`, `CrossInformationResult` |
| **Reportes** | `Report`, `ReportLogger`, `ReportLoggerFile` |
| **Procesos** | `BusinessProcess`, `ProcessLogger`, `SchedulerInfo` |
| **SMV** | `SmvInterface`, `SmvFilePolizas`, indicadores regulatorios |
| **Scoring** | `ScoringProcess`, `ScoringResult` |
| **Portal** | `PurchaseSaleOrder`, `ShoppingCart` |

### Patrones arquitectónicos identificados

```
JSF MgmtBean (@ViewScoped/@Named)
    └── inyecta → Facade (@Stateless @EJB)
            ├── inyecta → ServiceBean (@Stateless @EJB)
            │       └── inyecta → DAO (extends CrudDaoServiceBean @Stateless)
            │               └── usa → EntityManager (JPA)
            └── inyecta → BatchServiceBean (framework propio)
                    └── ejecuta → BatchProcess (paralelo/secuencial)

Eventos CDI:
    ServiceBean → Event<NotificationEvent> → BrowserWindow (SSE/Push)

Integración externa:
    Axis 1.4 SOAP → BCB (Banco Central Bolivia), EDV
    REST OkHttp/Jersey → HubSpot CRM
    SFTP JSch → Intercambio archivos SMV/UIF
```

---

## 2. Arquitectura Objetivo (React + Spring Boot)

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CLIENTE (Navegador)                             │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              React 18 + TypeScript (Vite)                    │   │
│  │                                                             │   │
│  │  ┌─────────────────────────────────────────────────────┐   │   │
│  │  │  Router (React Router 6)                            │   │   │
│  │  │  /holders   /accounts   /settlement   /plaft        │   │   │
│  │  │  /reports   /accounting   /batch   /parameters      │   │   │
│  │  └──────────────────────┬──────────────────────────────┘   │   │
│  │                          │                                  │   │
│  │  ┌───────────────────────▼──────────────────────────────┐  │   │
│  │  │              Pages / Features                         │  │   │
│  │  │  HoldersPage   AccountsPage   SettlementPage          │  │   │
│  │  │  PlaftPage     ReportsPage    BatchMonitorPage        │  │   │
│  │  └───────────────────────┬──────────────────────────────┘  │   │
│  │                          │                                  │   │
│  │  ┌────────────────────────────────────────────────────────┐│   │
│  │  │           Shared UI Components (Ant Design / MUI)      ││   │
│  │  │  DataTable  Modal  Form  FileUpload  Chart  Badge      ││   │
│  │  └────────────────────────────────────────────────────────┘│   │
│  │                          │                                  │   │
│  │  ┌────────────────────────────────────────────────────────┐│   │
│  │  │    State Management (React Query + Zustand)             ││   │
│  │  │    api.ts — axios interceptors + JWT refresh           ││   │
│  │  └────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTPS REST / WebSocket
┌──────────────────────────────▼──────────────────────────────────────┐
│                   Spring Boot 3.x (Jakarta EE 10)                   │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │             API Gateway Layer                                   │ │
│  │  SecurityConfig (JWT) │ CorsConfig │ GlobalExceptionHandler    │ │
│  │  OpenAPI/Swagger 3    │ RequestLoggingFilter                   │ │
│  └──────────────────────────────┬─────────────────────────────────┘ │
│                                 │                                    │
│  ┌──────────────────────────────▼─────────────────────────────────┐ │
│  │                  REST Controllers                               │ │
│  │  HolderController    │ HolderAccountController                 │ │
│  │  SettlementController│ PlaftController                         │ │
│  │  AccountingController│ ReportController                        │ │
│  │  BatchController     │ ParameterController                     │ │
│  │  AuthController      │ FileController                          │ │
│  └──────────────────────────────┬─────────────────────────────────┘ │
│                                 │                                    │
│  ┌──────────────────────────────▼─────────────────────────────────┐ │
│  │                  Service Layer (@Service)                       │ │
│  │  HolderService     │ HolderAccountService                      │ │
│  │  SettlementService │ AssetLaundryService                       │ │
│  │  AccountingService │ ReportService                             │ │
│  │  BatchJobService   │ NotificationService                       │ │
│  └──────────────────────────────┬─────────────────────────────────┘ │
│                                 │                                    │
│  ┌──────────────────────────────▼─────────────────────────────────┐ │
│  │            Repository Layer (Spring Data JPA)                   │ │
│  │  HolderRepository  │ HolderAccountRepository                   │ │
│  │  SettlementRepository│ AccountingRepository                    │ │
│  └──────────────────────────────┬─────────────────────────────────┘ │
│                                 │                                    │
│  ┌──────────────────────────────▼─────────────────────────────────┐ │
│  │                Domain Model (Jakarta Persistence)               │ │
│  │  Holder  HolderAccount  OperationSettlement  Accounting...     │ │
│  └──────────────────────────────┬─────────────────────────────────┘ │
│                                 │                                    │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │           Infrastructure / Integration                          │ │
│  │  Spring Batch     │ Spring WebSocket (SSE)                     │ │
│  │  Spring Mail      │ Spring Security (JWT)                      │ │
│  │  WebServiceClient │ HubSpotClient (OpenFeign)                  │ │
│  │  SftpService      │ JasperReportsService                       │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
               │                           │
          Oracle/PostgreSQL           File System / S3
```

---

## 3. Diagrama de Componentes — Módulo a Módulo

```
  ACTUAL                              OBJETIVO
  ══════                              ════════

iIntegration.jar                  → pradera-commons (lib compartida)
  Auditable.java                      @interface Auditable
  JWTConstants.java                   JwtProperties.java
  SystemConstants.java                ApplicationConstants.java
  ServiceException.java               (mantener, repackage a jakarta)
  Validations.java                    ValidationUtils.java
  IParameterTable.java                (mantener como interfaz)

iModel.jar                        → pradera-domain (lib compartida)
  javax.persistence.* → jakarta.persistence.*
  @Entity, @Table, @OneToMany       (sin cambios lógicos)
  Holder, HolderAccount...          (migrar anotaciones solamente)
  enums/types/*                     (sin cambios)

iCoreFramework.jar                → Spring Batch + Spring AOP
  BatchServiceBean (EJB)         →  BatchJobLauncher (@Component)
  BatchProcess (interfaz)        →  Tasklet / ItemProcessor
  ParallelWorkManager            →  TaskExecutor (ThreadPoolTask)
  SequentialWorkManager          →  Step secuencial Spring Batch
  AuditProcessLoggerInterceptor  →  @Around AOP + @Audit

iCommons.jar                      → pradera-commons-spring
  GenericBaseBean (JSF)          →  ← ELIMINAR (vista a React)
  DepositaryWebBean (JSF)        →  ← ELIMINAR
  JSFUtilities.java              →  ← ELIMINAR
  JWT (jjwt 0.7)                 →  jjwt 0.12 / spring-security-jwt
  SftpService (JSch)             →  SftpGateway (@Component)
  JasperReports service          →  ReportService (@Service)
  OkHttp client                  →  RestTemplate / WebClient

iCoreComponent.jar               → pradera-integration
  Axis 1.4 SOAP stubs            →  Spring WS / CXF (regenerar WSDL)
  ServiciosClienteBCB (Axis)     →  BcbSoapClient (@Component)
  ServiciosClienteEDV (Axis)     →  EdvSoapClient (@Component)
  QrGenerator                    →  QrService (@Component, ZXing)
  PdfBoxService                  →  DocumentService (@Component)
  AccountsFacade (EJB)           →  AccountsService (@Service)

iAccounts WAR                    → pradera-api (Spring Boot WAR/JAR)
  ─ view/* (JSF MgmtBeans)       →  REST Controllers + React Pages
  HolderMgmtBean                 →  HolderController + React HoldersPage
  AssetLaundryBean               →  PlaftController + React PlaftPage
  HolderAccountMgmtBean          →  AccountController + React AccountsPage
  HubspotSyncronizeMgmtBean      →  HubspotController + React HubspotPage

  ─ facade/* (EJB Stateless)     →  @Service (façade layer puede mantenerse
  HolderServiceFacade               como OrchestrationService)
  AssetLaundryFacade

  ─ service/* (EJB Stateless)    →  @Service
  HolderServiceBean              →  HolderService
  AssetLaundryServiceBean        →  AssetLaundryService

  ─ dao/* (EJB + CrudDaoSvcBean) →  @Repository (Spring Data JPA)
  HolderAccountDAO               →  HolderAccountRepository
  AccountStatementDAO            →  AccountStatementRepository

  ─ batch/* (EJB + BatchSvcBean) →  Spring Batch Jobs
  HolderCreationProcessBatch     →  HolderCreationJob
  AccountStateBatch              →  AccountStateJob
  PlafCrossInfoProcessBatch      →  PlaftCrossInfoJob
```

---

## 4. Estructura del Proyecto Objetivo

### 4.1 Backend — Spring Boot (Maven multi-módulo)

```
pradera-api/
├── pom.xml                              (parent pom, Spring Boot 3.3.x)
│
├── pradera-commons/                     ← iIntegration + partes de iCommons
│   └── src/main/java/com/pradera/
│       ├── commons/
│       │   ├── audit/
│       │   │   └── Auditable.java
│       │   ├── exception/
│       │   │   └── ServiceException.java
│       │   ├── jwt/
│       │   │   └── JwtProperties.java
│       │   ├── validation/
│       │   │   └── ValidationUtils.java
│       │   └── constants/
│       │       └── SystemConstants.java
│
├── pradera-domain/                      ← iModel (solo migrar javax → jakarta)
│   └── src/main/java/com/pradera/
│       └── model/
│           ├── accounts/
│           │   ├── Holder.java          (@Entity, jakarta.persistence.*)
│           │   ├── HolderAccount.java
│           │   └── holderaccounts/
│           ├── settlement/
│           ├── accounting/
│           ├── plaft/
│           └── process/
│
├── pradera-integration/                 ← iCoreComponent (clientes externos)
│   └── src/main/java/com/pradera/
│       └── integration/
│           ├── soap/
│           │   ├── bcb/
│           │   │   └── BcbSoapClient.java
│           │   └── edv/
│           │       └── EdvSoapClient.java
│           ├── hubspot/
│           │   └── HubSpotFeignClient.java  (@FeignClient)
│           ├── sftp/
│           │   └── SftpGateway.java
│           └── qr/
│               └── QrService.java
│
└── pradera-app/                         ← iAccounts (Spring Boot app)
    └── src/main/java/com/pradera/
        ├── PraderaApplication.java
        ├── config/
        │   ├── SecurityConfig.java
        │   ├── CorsConfig.java
        │   ├── BatchConfig.java
        │   ├── WebSocketConfig.java
        │   └── OpenApiConfig.java
        ├── controller/
        │   ├── AuthController.java
        │   ├── HolderController.java
        │   ├── HolderAccountController.java
        │   ├── SettlementController.java
        │   ├── PlaftController.java
        │   ├── AccountingController.java
        │   ├── ReportController.java
        │   ├── BatchController.java
        │   ├── ParameterController.java
        │   └── FileController.java
        ├── dto/
        │   ├── holder/
        │   │   ├── HolderRequestDTO.java
        │   │   └── HolderResponseDTO.java
        │   ├── account/
        │   ├── settlement/
        │   └── plaft/
        ├── service/
        │   ├── HolderService.java
        │   ├── HolderAccountService.java
        │   ├── AssetLaundryService.java
        │   ├── SettlementService.java
        │   ├── AccountingService.java
        │   ├── ReportService.java
        │   └── NotificationService.java
        ├── repository/
        │   ├── HolderRepository.java
        │   ├── HolderAccountRepository.java
        │   └── AccountStatementRepository.java
        ├── batch/
        │   ├── HolderCreationJob.java
        │   ├── AccountStateJob.java
        │   └── PlaftCrossInfoJob.java
        └── exception/
            └── GlobalExceptionHandler.java
```

### 4.2 Frontend — React + TypeScript

```
pradera-web/
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── api/
│   │   ├── client.ts              (axios + interceptors JWT)
│   │   ├── holders.api.ts
│   │   ├── accounts.api.ts
│   │   ├── settlement.api.ts
│   │   ├── plaft.api.ts
│   │   └── reports.api.ts
│   ├── auth/
│   │   ├── AuthProvider.tsx
│   │   └── useAuth.ts
│   ├── features/
│   │   ├── holders/
│   │   │   ├── HoldersPage.tsx         ← HolderMgmtBean + XHTML
│   │   │   ├── HolderForm.tsx          ← HolderRequestAppFormMgmtBean
│   │   │   ├── HolderSearchPanel.tsx   ← SearchHolderMgmtBean
│   │   │   ├── HolderDataTable.tsx     ← HolderDataModel (PF DataTable)
│   │   │   └── hooks/
│   │   │       └── useHolders.ts       (React Query)
│   │   ├── accounts/
│   │   │   ├── AccountsPage.tsx        ← HolderAccountMgmtBean
│   │   │   ├── AccountModifyForm.tsx   ← HolderAccountModifyMgmtBean
│   │   │   └── AccountBlockModal.tsx   ← HolderAccountBlockMgmtBean
│   │   ├── plaft/
│   │   │   ├── PlaftPage.tsx           ← AssetLaundryBean
│   │   │   ├── OfacSearchPanel.tsx     ← OfacPersonDataModel
│   │   │   ├── PepSearchPanel.tsx      ← PepPersonDataModel
│   │   │   └── PnaSearchPanel.tsx      ← PnaPersonDatamodel
│   │   ├── settlement/
│   │   │   └── SettlementPage.tsx
│   │   ├── reports/
│   │   │   └── ReportsPage.tsx
│   │   ├── batch/
│   │   │   └── BatchMonitorPage.tsx
│   │   └── hubspot/
│   │       └── HubspotSyncPage.tsx     ← HubspotSyncronizeMgmtBean
│   ├── components/
│   │   ├── DataTable/
│   │   │   └── ServerDataTable.tsx    (paginación servidor, = PF lazy)
│   │   ├── FileUpload/
│   │   │   └── FileUploader.tsx       (= PF FileUpload)
│   │   ├── Modal/
│   │   └── Layout/
│   │       ├── MainLayout.tsx
│   │       ├── Sidebar.tsx
│   │       └── TopBar.tsx
│   ├── hooks/
│   │   ├── useDataTable.ts
│   │   └── useWebSocket.ts            (reemplaza CDI push events)
│   └── types/
│       ├── holder.types.ts
│       ├── account.types.ts
│       └── plaft.types.ts
├── vite.config.ts
└── package.json
```

---

## 5. Patrones de Migración Concretos

### 5.1 EJB @Stateless → Spring @Service

**ANTES (iAccounts — Java EE):**
```java
@Stateless
@TransactionAttribute(TransactionAttributeType.REQUIRED)
public class HolderAccountDAO extends CrudDaoServiceBean {

    @Inject
    private UserInfo userInfo;

    public List<HolderAccount> allByParticipant(
            Participant participant,
            HolderAccountStatusType... statuses) {

        StringBuilder q = new StringBuilder();
        q.append("SELECT ha FROM HolderAccount ha ");
        q.append("JOIN ha.participant p WHERE p.idParticipantPk=:PARTICIPANT ");
        // ...
        return super.listByQueryString(q.toString(), params);
    }
}
```

**DESPUÉS (Spring Boot):**
```java
@Repository
public interface HolderAccountRepository
        extends JpaRepository<HolderAccount, Long> {

    @Query("""
        SELECT ha FROM HolderAccount ha
        JOIN ha.participant p
        WHERE p.idParticipantPk = :participantId
        AND (:#{#statuses == null} = true OR ha.stateAccount IN :statuses)
        """)
    List<HolderAccount> findByParticipant(
        @Param("participantId") Long participantId,
        @Param("statuses") List<Integer> statuses
    );
}
```

---

### 5.2 JSF MgmtBean (@ViewScoped) → REST Controller + React Page

**ANTES (iAccounts — HolderMgmtBean.java, ViewScoped JSF):**
```java
@Named
@ViewScoped
public class HolderMgmtBean extends GenericBaseBean implements Serializable {

    @EJB
    private HolderServiceFacade holderServiceFacade;

    private List<Holder> holderList;
    private Holder selectedHolder;

    @PostConstruct
    public void init() {
        holderList = holderServiceFacade.findAll();
    }

    public void searchHolder() {
        // modifica holderList, actualiza DataTable PrimeFaces
    }

    public void saveHolder() {
        holderServiceFacade.save(selectedHolder);
        JSFUtilities.addMessage("Titular registrado");
    }
}
```

**DESPUÉS (Spring Boot — Controller):**
```java
@RestController
@RequestMapping("/api/v1/holders")
@RequiredArgsConstructor
public class HolderController {

    private final HolderService holderService;

    @GetMapping
    public Page<HolderResponseDTO> search(
            @ModelAttribute HolderSearchDTO filter,
            Pageable pageable) {
        return holderService.search(filter, pageable);
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public HolderResponseDTO create(@Valid @RequestBody HolderRequestDTO dto) {
        return holderService.create(dto);
    }

    @PutMapping("/{id}")
    public HolderResponseDTO update(
            @PathVariable Long id,
            @Valid @RequestBody HolderRequestDTO dto) {
        return holderService.update(id, dto);
    }

    @PatchMapping("/{id}/block")
    public void block(@PathVariable Long id,
                      @RequestBody BlockRequestDTO dto) {
        holderService.block(id, dto);
    }
}
```

**DESPUÉS (React — HoldersPage.tsx):**
```tsx
// Reemplaza HolderMgmtBean + holders.xhtml + PrimeFaces DataTable

const HoldersPage: React.FC = () => {
  const [filter, setFilter] = useState<HolderFilter>({});

  const { data, isLoading } = useQuery({
    queryKey: ['holders', filter],
    queryFn: () => holdersApi.search(filter),
  });

  const createMutation = useMutation({
    mutationFn: holdersApi.create,
    onSuccess: () => queryClient.invalidateQueries(['holders']),
  });

  return (
    <MainLayout>
      <HolderSearchPanel onSearch={setFilter} />
      <ServerDataTable
        data={data?.content}
        loading={isLoading}
        columns={holderColumns}
        actions={<HolderActions onCreate={() => setModalOpen(true)} />}
      />
      <HolderFormModal onSubmit={createMutation.mutate} />
    </MainLayout>
  );
};
```

---

### 5.3 EJB Batch → Spring Batch

**ANTES (iAccounts — HolderCreationProcessBatch.java):**
```java
@Stateless
public class HolderCreationProcessBatch {

    @EJB
    private BatchServiceBean batchServiceBean;

    @EJB
    private HolderServiceBean holderServiceBean;

    public void execute(List<MassiveHolderTO> holders) {
        batchServiceBean.executeParallel(holders, holder -> {
            holderServiceBean.createHolder(holder);
        });
    }
}
```

**DESPUÉS (Spring Batch):**
```java
@Configuration
@RequiredArgsConstructor
public class HolderCreationJobConfig {

    private final JobRepository jobRepository;
    private final PlatformTransactionManager txManager;
    private final HolderService holderService;

    @Bean
    public Job holderCreationJob(Step holderCreationStep) {
        return new JobBuilder("holderCreationJob", jobRepository)
                .start(holderCreationStep)
                .build();
    }

    @Bean
    public Step holderCreationStep() {
        return new StepBuilder("holderCreationStep", jobRepository)
                .<MassiveHolderDTO, Holder>chunk(50, txManager)
                .reader(holderItemReader())
                .processor(holderItemProcessor())
                .writer(holderItemWriter())
                .taskExecutor(taskExecutor())
                .build();
    }

    @Bean
    public TaskExecutor taskExecutor() {
        ThreadPoolTaskExecutor exec = new ThreadPoolTaskExecutor();
        exec.setCorePoolSize(4);
        exec.setMaxPoolSize(8);
        return exec;
    }

    @Bean
    public ItemProcessor<MassiveHolderDTO, Holder> holderItemProcessor() {
        return holderService::processHolder;
    }
}
```

---

### 5.4 Axis 1.4 SOAP → Spring WS / CXF

**ANTES (iCoreComponent — Axis 1.4, auto-generado):**
```java
// ServiciosClienteBCBServiceSoapBindingStub (Axis 1.4 auto-generated)
public class ServiciosClienteBCBServiceSoapBindingStub
        extends org.apache.axis.client.Stub {
    // Código generado, difícil de mantener
}
```

**DESPUÉS (Spring WS):**
```java
// 1. Regenerar desde WSDL con wsimport o wsdl2java (CXF)
// 2. Envolver en cliente limpio

@Component
public class BcbSoapClient {

    private final ServiciosClienteBCB stub;

    public BcbSoapClient(@Value("${bcb.soap.endpoint}") String endpoint) {
        // JAX-WS stub generado por wsimport (javax → jakarta)
        ServiciosClienteBCBService service = new ServiciosClienteBCBService();
        this.stub = service.getPort(ServiciosClienteBCB.class);
        ((BindingProvider) stub).getRequestContext()
            .put(BindingProvider.ENDPOINT_ADDRESS_PROPERTY, endpoint);
    }

    public ConsultaClienteResponse consultarCliente(String documentNumber) {
        return stub.consultarCliente(documentNumber);
    }
}
```

---

### 5.5 CDI Event Push → Spring WebSocket (SSE)

**ANTES (CDI Browser Push — iAccounts):**
```java
@Inject
private Event<NotificationEvent> notificationEvent;

// En HolderServiceFacade:
notificationEvent.fire(new NotificationEvent(
    NotificationType.HOLDER_CREATED, holderId));
```

**DESPUÉS (Spring SSE):**
```java
// Backend
@RestController
@RequestMapping("/api/v1/notifications")
public class NotificationController {

    private final SseEmitterService emitterService;

    @GetMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter stream(Authentication auth) {
        return emitterService.createEmitter(auth.getName());
    }
}

// Service emite al completar una operación
holderRepository.save(holder);
emitterService.emit(userId, new NotificationEvent("HOLDER_CREATED", holder.getId()));
```

```tsx
// Frontend React
const useNotifications = () => {
  useEffect(() => {
    const es = new EventSource('/api/v1/notifications/stream');
    es.onmessage = (e) => {
      const event = JSON.parse(e.data);
      toast.success(`Operación completada: ${event.type}`);
    };
    return () => es.close();
  }, []);
};
```

---

### 5.6 JWT: jjwt 0.7 → Spring Security + jjwt 0.12

**ANTES (iCommons — JWT 0.7):**
```java
// Sintaxis antigua, API deprecada
String token = Jwts.builder()
    .setSubject(username)
    .signWith(SignatureAlgorithm.HS512, secret)
    .compact();
```

**DESPUÉS (Spring Security + jjwt 0.12):**
```java
@Component
public class JwtTokenProvider {

    @Value("${jwt.secret}") private String secret;
    @Value("${jwt.expiration}") private long expiration;

    public String generate(UserDetails user) {
        SecretKey key = Keys.hmacShaKeyFor(secret.getBytes());
        return Jwts.builder()
                .subject(user.getUsername())
                .issuedAt(new Date())
                .expiration(new Date(System.currentTimeMillis() + expiration))
                .signWith(key)
                .compact();
    }

    public String extractUsername(String token) {
        return Jwts.parser()
                .verifyWith(Keys.hmacShaKeyFor(secret.getBytes()))
                .build()
                .parseSignedClaims(token)
                .getPayload()
                .getSubject();
    }
}
```

---

## 6. Plan de Migración por Fases

### Fase 0 — Preparación y Baseline (Semanas 1–2)

| Tarea | Módulo | Prioridad |
|---|---|---|
| Crear repo Git monorepo `pradera-api` + `pradera-web` | Todos | Alta |
| Configurar parent POM Spring Boot 3.3.x | Backend | Alta |
| Habilitar Jakarta EE 10 (javax → jakarta) en iModel | iModel | Alta |
| Setup React + Vite + TypeScript + React Query + Zustand | Frontend | Alta |
| Definir OpenAPI spec (contratos REST) antes de codear | Backend | Alta |
| Configurar CI/CD (GitHub Actions: build, test, sonar) | DevOps | Media |
| Inventariar todas las páginas XHTML → mapear a rutas React | iAccounts/view | Alta |

**Entregable:** Proyectos compilando, iModel migrando anotaciones, spec OpenAPI v1.

---

### Fase 1 — Migrar iModel + iIntegration (Semanas 2–3)

**Objetivo:** Base del dominio funcional en Jakarta.

```java
// Único cambio en cada entidad:
// ANTES:
import javax.persistence.*;
// DESPUÉS:
import jakarta.persistence.*;

// Mismo para CDI:
// javax.enterprise.* → jakarta.enterprise.*
// javax.inject.* → jakarta.inject.*
// javax.transaction.* → jakarta.transaction.*
```

**Script de migración masiva:**
```bash
# Reemplazar imports en todo iModel y iIntegration
find . -name "*.java" -not -path "*/target/*" \
  -exec sed -i 's/javax\.persistence\./jakarta.persistence./g' {} \;
find . -name "*.java" -not -path "*/target/*" \
  -exec sed -i 's/javax\.inject\./jakarta.inject./g' {} \;
find . -name "*.java" -not -path "*/target/*" \
  -exec sed -i 's/javax\.transaction\./jakarta.transaction./g' {} \;
find . -name "*.java" -not -path "*/target/*" \
  -exec sed -i 's/javax\.enterprise\./jakarta.enterprise./g' {} \;
```

**Entregable:** `pradera-domain` compila con Spring Boot 3.x / Jakarta.

---

### Fase 2 — Backend Core: Auth + Holders + Accounts (Semanas 3–6)

**Objetivo:** API REST funcional para los flujos principales.

#### 2.1 Configuración Spring Security (reemplaza JWT manual de iCommons)

```java
@Configuration
@EnableWebSecurity
@RequiredArgsConstructor
public class SecurityConfig {

    private final JwtAuthenticationFilter jwtFilter;

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
            .csrf(AbstractHttpConfigurer::disable)
            .sessionManagement(s -> s.sessionCreationPolicy(STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/v1/auth/**").permitAll()
                .requestMatchers("/actuator/health").permitAll()
                .anyRequest().authenticated()
            )
            .addFilterBefore(jwtFilter, UsernamePasswordAuthenticationFilter.class)
            .build();
    }
}
```

#### 2.2 Repositories (reemplazan DAOs + CrudDaoServiceBean)

```java
// HolderRepository — reemplaza HolderAccountDAO
@Repository
public interface HolderRepository extends JpaRepository<Holder, Long> {

    @Query("""
        SELECT h FROM Holder h
        LEFT JOIN FETCH h.holderAccounts
        WHERE h.documentNumber = :doc
        AND h.participantId = :participantId
        """)
    Optional<Holder> findByDocumentAndParticipant(
        @Param("doc") String doc,
        @Param("participantId") Long participantId
    );

    @Query("""
        SELECT h FROM Holder h
        WHERE (:name IS NULL OR UPPER(h.fullName) LIKE UPPER(CONCAT('%',:name,'%')))
        AND (:state IS NULL OR h.holderState = :state)
        AND h.participantId = :participantId
        """)
    Page<Holder> searchWithFilters(
        @Param("name") String name,
        @Param("state") Integer state,
        @Param("participantId") Long participantId,
        Pageable pageable
    );
}
```

#### 2.3 Service Layer

```java
@Service
@Transactional
@RequiredArgsConstructor
public class HolderService {

    private final HolderRepository holderRepository;
    private final HolderAccountRepository accountRepository;
    private final NotificationService notificationService;
    private final HolderMapper mapper;

    public HolderResponseDTO create(HolderRequestDTO dto) {
        validateHolder(dto);
        Holder holder = mapper.toEntity(dto);
        holder = holderRepository.save(holder);
        notificationService.emit(
            dto.getOperatorId(),
            "HOLDER_CREATED", holder.getIdHolderPk()
        );
        return mapper.toDTO(holder);
    }

    public Page<HolderResponseDTO> search(HolderSearchDTO filter, Pageable pageable) {
        return holderRepository
            .searchWithFilters(filter.getName(), filter.getState(),
                              filter.getParticipantId(), pageable)
            .map(mapper::toDTO);
    }

    @Transactional(readOnly = true)
    public HolderResponseDTO findById(Long id) {
        return holderRepository.findById(id)
            .map(mapper::toDTO)
            .orElseThrow(() -> new EntityNotFoundException("Holder " + id));
    }
}
```

**Entregable Fase 2:** APIs de Holders y Accounts operativas con Swagger UI.

---

### Fase 3 — Backend Avanzado: PLAFT + Settlement + Accounting (Semanas 7–10)

**Objetivo:** Módulos regulatorios y financieros.

#### 3.1 Módulo PLAFT (Asset Laundry — reemplaza AssetLaundryFacade)

```java
@RestController
@RequestMapping("/api/v1/plaft")
@RequiredArgsConstructor
public class PlaftController {

    private final AssetLaundryService assetLaundryService;

    @PostMapping("/ofac/cross-check")
    public ResponseEntity<PlaftResultDTO> ofacCrossCheck(
            @Valid @RequestBody PlaftCrossCheckDTO dto) {
        return ResponseEntity.ok(assetLaundryService.ofacCrossCheck(dto));
    }

    @PostMapping("/pep/cross-check")
    public ResponseEntity<PlaftResultDTO> pepCrossCheck(
            @Valid @RequestBody PlaftCrossCheckDTO dto) {
        return ResponseEntity.ok(assetLaundryService.pepCrossCheck(dto));
    }

    @GetMapping("/uif/report/{holderId}")
    public ResponseEntity<Resource> generateUifReport(
            @PathVariable Long holderId) {
        byte[] pdf = assetLaundryService.generateUifReport(holderId);
        return ResponseEntity.ok()
            .contentType(MediaType.APPLICATION_PDF)
            .body(new ByteArrayResource(pdf));
    }
}
```

#### 3.2 Spring Batch — Reemplaza BatchServiceBean

```java
// Controller para trigger manual de batch (reemplaza JSF batch buttons)
@RestController
@RequestMapping("/api/v1/batch")
@RequiredArgsConstructor
public class BatchController {

    private final JobLauncher jobLauncher;
    private final Job holderCreationJob;
    private final Job accountStateJob;
    private final Job plaftCrossInfoJob;

    @PostMapping("/holder-creation/run")
    public ResponseEntity<String> runHolderCreation() throws Exception {
        JobParameters params = new JobParametersBuilder()
            .addDate("runDate", new Date())
            .toJobParameters();
        JobExecution execution = jobLauncher.run(holderCreationJob, params);
        return ResponseEntity.accepted().body(execution.getJobId().toString());
    }

    @GetMapping("/jobs/{jobId}/status")
    public BatchJobStatusDTO getStatus(@PathVariable Long jobId) {
        // Spring Batch JobRepository query
    }
}
```

**Entregable Fase 3:** PLAFT, Liquidaciones y Contabilidad con tests de integración.

---

### Fase 4 — Frontend React (Semanas 6–12, paralelo al backend)

**Objetivo:** SPA React que reemplaza todas las páginas XHTML/PrimeFaces.

#### 4.1 Tabla de conversión XHTML → React

| Componente PrimeFaces | Equivalente React |
|---|---|
| `<p:dataTable lazy paginator>` | `ServerDataTable` (TanStack Table) |
| `<p:dialog modal>` | Modal (Ant Design / shadcn) |
| `<p:fileUpload>` | `FileUploader` (react-dropzone) |
| `<p:chart type="bar">` | Recharts / ECharts |
| `<p:autoComplete>` | Combobox (react-select) |
| `<p:messages/p:growl>` | react-hot-toast |
| `<p:commandButton ajax>` | Button + useMutation |
| `<p:tree>` | Tree component (Ant Design) |
| `<p:pickList>` | DualList (custom) |
| `<p:poll>` | useWebSocket / EventSource SSE |

#### 4.2 Cliente API con interceptores JWT

```ts
// src/api/client.ts
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  timeout: 30000,
});

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

apiClient.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

#### 4.3 ServerDataTable con paginación server-side

```tsx
// Reemplaza PrimeFaces p:dataTable lazy
interface ServerDataTableProps<T> {
  queryKey: string[];
  fetchFn: (params: TableParams) => Promise<Page<T>>;
  columns: ColumnDef<T>[];
}

function ServerDataTable<T>({ queryKey, fetchFn, columns }: ServerDataTableProps<T>) {
  const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: 20 });
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);

  const { data, isLoading } = useQuery({
    queryKey: [...queryKey, pagination, sorting, columnFilters],
    queryFn: () => fetchFn({ pagination, sorting, columnFilters }),
  });

  const table = useReactTable({
    data: data?.content ?? [],
    columns,
    pageCount: data?.totalPages ?? -1,
    manualPagination: true,
    manualSorting: true,
    state: { pagination, sorting, columnFilters },
    onPaginationChange: setPagination,
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
  });

  return <DataTable table={table} loading={isLoading} />;
}
```

---

### Fase 5 — Integración SOAP/External + JasperReports (Semanas 10–13)

#### 5.1 Reemplazar Apache Axis 1.4

```xml
<!-- pom.xml: reemplaza Axis 1.4 -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web-services</artifactId>
</dependency>
<!-- o CXF para más control -->
<dependency>
    <groupId>org.apache.cxf</groupId>
    <artifactId>cxf-spring-boot-starter-jaxws</artifactId>
    <version>4.0.x</version>
</dependency>
```

```bash
# Regenerar stubs desde WSDL (JAX-WS, Jakarta namespace)
wsimport -target 3.0 -keep -s src/main/java \
  http://bcb.endpoint/ServiciosClienteBCB?wsdl
```

#### 5.2 JasperReports → ReportService

```java
@Service
@RequiredArgsConstructor
public class ReportService {

    @Value("classpath:reports/")
    private Resource reportsPath;

    public byte[] generatePdf(String reportName, Map<String, Object> params,
                              JRDataSource dataSource) {
        try {
            InputStream stream = reportsPath
                .createRelative(reportName + ".jasper")
                .getInputStream();
            JasperPrint print = JasperFillManager.fillReport(
                stream, params, dataSource);
            return JasperExportManager.exportReportToPdf(print);
        } catch (JRException | IOException e) {
            throw new ReportGenerationException(reportName, e);
        }
    }
}
```

---

### Fase 6 — Containerización y Go-Live (Semanas 14–16)

#### 6.1 Dockerfiles

```dockerfile
# pradera-app/Dockerfile (Spring Boot)
FROM eclipse-temurin:21-jdk-alpine AS build
WORKDIR /app
COPY pom.xml .
COPY src ./src
RUN mvn package -DskipTests -pl pradera-app -am

FROM eclipse-temurin:21-jre-alpine
RUN addgroup -S pradera && adduser -S pradera -G pradera
USER pradera
WORKDIR /app
COPY --from=build /app/pradera-app/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-Djava.security.egd=file:/dev/./urandom", "-jar", "app.jar"]
```

```dockerfile
# pradera-web/Dockerfile (React)
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

#### 6.2 Docker Compose

```yaml
services:
  pradera-web:
    build: ./pradera-web
    ports: ["80:80"]
    depends_on: [pradera-api]
    environment:
      VITE_API_URL: http://pradera-api:8080

  pradera-api:
    build: ./pradera-app
    ports: ["8080:8080"]
    environment:
      SPRING_DATASOURCE_URL: jdbc:postgresql://db:5432/pradera
      SPRING_DATASOURCE_USERNAME: ${DB_USER}
      SPRING_DATASOURCE_PASSWORD: ${DB_PASS}
      JWT_SECRET: ${JWT_SECRET}
      BCB_SOAP_ENDPOINT: ${BCB_ENDPOINT}
      HUBSPOT_API_KEY: ${HUBSPOT_KEY}
    depends_on: [db]

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: pradera
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASS}
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

---

## 7. Dependencias del Proyecto Objetivo

### Backend `pom.xml` (pradera-app)

```xml
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.3.4</version>
</parent>

<dependencies>
    <!-- Web -->
    <dependency><groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId></dependency>

    <!-- Security + JWT -->
    <dependency><groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-security</artifactId></dependency>
    <dependency><groupId>io.jsonwebtoken</groupId>
        <artifactId>jjwt-api</artifactId><version>0.12.6</version></dependency>
    <dependency><groupId>io.jsonwebtoken</groupId>
        <artifactId>jjwt-impl</artifactId><version>0.12.6</version></dependency>

    <!-- JPA -->
    <dependency><groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-data-jpa</artifactId></dependency>
    <dependency><groupId>org.postgresql</groupId>
        <artifactId>postgresql</artifactId></dependency>

    <!-- Validation -->
    <dependency><groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-validation</artifactId></dependency>

    <!-- Batch -->
    <dependency><groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-batch</artifactId></dependency>

    <!-- WebSocket / SSE -->
    <dependency><groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-websocket</artifactId></dependency>

    <!-- Mail -->
    <dependency><groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-mail</artifactId></dependency>

    <!-- Actuator -->
    <dependency><groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-actuator</artifactId></dependency>

    <!-- OpenAPI -->
    <dependency><groupId>org.springdoc</groupId>
        <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
        <version>2.6.0</version></dependency>

    <!-- OpenFeign (HubSpot) -->
    <dependency><groupId>org.springframework.cloud</groupId>
        <artifactId>spring-cloud-starter-openfeign</artifactId></dependency>

    <!-- SOAP (reemplaza Axis) -->
    <dependency><groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web-services</artifactId></dependency>

    <!-- JasperReports -->
    <dependency><groupId>net.sf.jasperreports</groupId>
        <artifactId>jasperreports</artifactId><version>6.21.0</version></dependency>

    <!-- SFTP (reemplaza JSch) -->
    <dependency><groupId>org.springframework.integration</groupId>
        <artifactId>spring-integration-sftp</artifactId></dependency>

    <!-- MapStruct -->
    <dependency><groupId>org.mapstruct</groupId>
        <artifactId>mapstruct</artifactId><version>1.6.0</version></dependency>

    <!-- Lombok -->
    <dependency><groupId>org.projectlombok</groupId>
        <artifactId>lombok</artifactId><scope>provided</scope></dependency>

    <!-- Tests -->
    <dependency><groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-test</artifactId><scope>test</scope></dependency>
    <dependency><groupId>org.springframework.security</groupId>
        <artifactId>spring-security-test</artifactId><scope>test</scope></dependency>
    <dependency><groupId>org.springframework.batch</groupId>
        <artifactId>spring-batch-test</artifactId><scope>test</scope></dependency>
</dependencies>
```

### Frontend `package.json`

```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.26.0",
    "@tanstack/react-query": "^5.56.0",
    "@tanstack/react-table": "^8.20.0",
    "zustand": "^5.0.0",
    "axios": "^1.7.0",
    "antd": "^5.21.0",
    "recharts": "^2.13.0",
    "react-hot-toast": "^2.4.0",
    "react-hook-form": "^7.53.0",
    "zod": "^3.23.0",
    "@hookform/resolvers": "^3.9.0",
    "react-dropzone": "^14.3.0",
    "dayjs": "^1.11.0"
  },
  "devDependencies": {
    "typescript": "^5.5.0",
    "vite": "^5.4.0",
    "@vitejs/plugin-react": "^4.3.0",
    "@types/react": "^18.3.0"
  }
}
```

---

## 8. Cronograma Completo

```
         S1   S2   S3   S4   S5   S6   S7   S8   S9  S10  S11  S12  S13  S14  S15  S16
Fase 0   ████ ████
Fase 1        ████ ████
Fase 2             ████ ████ ████ ████
Fase 4 (FE)             ████ ████ ████ ████ ████ ████ ████ ████ ████
Fase 3                             ████ ████ ████ ████
Fase 5                                            ████ ████ ████
Fase 6                                                       ████ ████ ████
Tests                                        ████ ████ ████ ████ ████
UAT                                                               ████ ████
Go-Live                                                                    ██
```

**Duración estimada: 16 semanas (4 meses)**  
**Equipo recomendado:** 2 backend Java, 2 frontend React, 1 QA, 1 DevOps/arquitecto

---

## 9. Riesgos y Mitigaciones

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Axis 1.4 SOAP → WSDL no disponible | Alto | Obtener WSDLs de BCB/EDV antes de Fase 5; usar WireMock para tests |
| iModel: entidades con lógica de negocio embebida | Alto | Auditar cada entidad; extraer lógica a services |
| PrimeFaces DataTable lazy mode complejo | Medio | Mapear cada DataModel a ServerDataTable antes de codear |
| Batch jobs: orden y dependencia de pasos | Alto | Documentar DAG de dependencias antes de migrar a Spring Batch |
| CrudDaoServiceBean personalizado: métodos propios | Medio | Implementar como default methods en repositorios custom |
| JWT custom (UserInfo EJB session) | Medio | Migrar a Spring Security principal + JwtFilter desde Fase 2 |
| JasperReports: versión 6.11 → 6.21 API changes | Bajo | Test de regresión de reportes críticos (UIF, SMV) |
| Transacciones distribuidas (EJB TX propagation) | Alto | Replicar con @Transactional + transaction propagation explícita |

---

## 10. Checklist de Migración

### Backend
- [ ] `pradera-domain`: todos los imports `javax.persistence.*` → `jakarta.persistence.*`
- [ ] `pradera-commons`: ServiceException, Validations, JWT migrado a Spring Security
- [ ] `HolderRepository` reemplaza `HolderAccountDAO` + `CrudDaoServiceBean`
- [ ] `HolderService` reemplaza `HolderServiceBean` + `HolderServiceFacade`
- [ ] `HolderController` expone CRUD + search paginado
- [ ] `PlaftController` con endpoints OFAC, PEP, PNA, UIF
- [ ] `SettlementController` + `SettlementService`
- [ ] `AccountingController` + `AccountingService`
- [ ] Spring Batch: `HolderCreationJob`, `AccountStateJob`, `PlaftCrossInfoJob`
- [ ] `BcbSoapClient` + `EdvSoapClient` (Jakarta JAX-WS)
- [ ] `HubSpotFeignClient` reemplaza `HubspotService` (OkHttp)
- [ ] `ReportService` (JasperReports 6.21)
- [ ] `SftpGateway` reemplaza JSch manual
- [ ] Spring Security + JWT 0.12 (reemplaza jjwt 0.7)
- [ ] SSE `NotificationController` (reemplaza CDI events push)
- [ ] `GlobalExceptionHandler` con respuestas consistentes
- [ ] Tests unitarios: 80%+ coverage en services
- [ ] Tests de integración: controllers + repositorios
- [ ] `application.yml` con perfiles dev/staging/prod

### Frontend React
- [ ] AuthProvider + login page + JWT refresh interceptor
- [ ] `HoldersPage` (lista + búsqueda + paginación server)
- [ ] `HolderFormModal` (creación/edición — todos los campos del MgmtBean)
- [ ] `HolderAccountsPage` con bloqueo/desbloqueo
- [ ] `PlaftPage` con paneles OFAC, PEP, PNA
- [ ] `AccountStatementPage`
- [ ] `SettlementPage`
- [ ] `ReportsPage` con descarga PDF
- [ ] `BatchMonitorPage` con estado de jobs en tiempo real (SSE)
- [ ] `HubspotSyncPage`
- [ ] `ServerDataTable` (reemplaza todas las PF DataTables lazy)
- [ ] `FileUploader` (reemplaza PF FileUpload)
- [ ] Notificaciones SSE conectadas
- [ ] Roles/permisos (reemplaza `UserPrivilege` + `PrivilegeComponent`)

### DevOps
- [ ] `Dockerfile` multi-stage backend + frontend
- [ ] `docker-compose.yml` con PostgreSQL
- [ ] Variables de entorno documentadas en `.env.example`
- [ ] GitHub Actions: lint + test + build en PR
- [ ] GitHub Actions: deploy automático a staging en merge main
- [ ] Healthcheck `/actuator/health` en load balancer

---

*Generado por Claude Sonnet 4.6 — Arquitecto de Software*  
*Sistema analizado: iDepositary (Pradera) — 2.295 archivos Java, 331 páginas XHTML*
