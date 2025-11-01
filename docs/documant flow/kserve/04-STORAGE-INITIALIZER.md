# Storage Initializer

## Overview

The Storage Initializer is an init container in KServe that downloads model artifacts from various storage backends before the main inference containers start. It supports multiple protocols including S3, GCS, Azure Blob Storage, HTTP/HTTPS, and PVC.

## Storage Initializer Architecture

```mermaid
flowchart TB
    Start([Pod Initialization])
    
    subgraph InitContainer["Storage Initializer Init Container"]
        ParseConfig[Parse Storage Configuration]
        DetectProtocol{Detect Storage Protocol}
        
        subgraph S3Handler["S3 and MinIO Handler"]
            S3Config[Configure S3 Client]
            S3Auth[AWS Credentials Auth]
            S3List[List Objects]
            S3Download[Download Objects]
            S3Verify[Verify Checksums]
        end
        
        subgraph GCSHandler["Google Cloud Storage Handler"]
            GCSConfig[Configure GCS Client]
            GCSAuth[GCP Service Account Auth]
            GCSList[List Objects]
            GCSDownload[Download Objects]
            GCSVerify[Verify Integrity]
        end
        
        subgraph AzureHandler["Azure Blob Storage Handler"]
            AzureConfig[Configure Azure Client]
            AzureAuth[Azure Credentials Auth]
            AzureList[List Blobs]
            AzureDownload[Download Blobs]
            AzureVerify[Verify Integrity]
        end
        
        subgraph HTTPHandler["HTTP and HTTPS Handler"]
            HTTPConfig[Configure HTTP Client]
            HTTPAuth[Authentication Headers]
            HTTPDownload[Download via GET]
            HTTPVerify[Verify Content]
        end
        
        subgraph PVCHandler["PVC Handler"]
            PVCMount[Mount PVC]
            PVCCopy[Copy Files]
            PVCVerify[Verify Copy]
        end
        
        ExtractArchive[Extract Archives<br/>zip, tar, tar.gz]
        ValidateModel[Validate Model Structure]
        SetPermissions[Set File Permissions]
        SaveCache[Save to /mnt/models]
    end
    
    Complete([Init Complete])
    StartMainContainers[Start Main Containers]
    
    Start --> ParseConfig
    ParseConfig --> DetectProtocol
    
    DetectProtocol -->|s3| S3Config
    DetectProtocol -->|gs| GCSConfig
    DetectProtocol -->|azure blob| AzureConfig
    DetectProtocol -->|http/https| HTTPConfig
    DetectProtocol -->|pvc| PVCMount
    
    S3Config --> S3Auth
    S3Auth --> S3List
    S3List --> S3Download
    S3Download --> S3Verify
    S3Verify --> ExtractArchive
    
    GCSConfig --> GCSAuth
    GCSAuth --> GCSList
    GCSList --> GCSDownload
    GCSDownload --> GCSVerify
    GCSVerify --> ExtractArchive
    
    AzureConfig --> AzureAuth
    AzureAuth --> AzureList
    AzureList --> AzureDownload
    AzureDownload --> AzureVerify
    AzureVerify --> ExtractArchive
    
    HTTPConfig --> HTTPAuth
    HTTPAuth --> HTTPDownload
    HTTPDownload --> HTTPVerify
    HTTPVerify --> ExtractArchive
    
    PVCMount --> PVCCopy
    PVCCopy --> PVCVerify
    PVCVerify --> ExtractArchive
    
    ExtractArchive --> ValidateModel
    ValidateModel --> SetPermissions
    SetPermissions --> SaveCache
    SaveCache --> Complete
    Complete --> StartMainContainers
    
    style InitContainer fill:#e1f5ff
    style S3Handler fill:#fff4e1
    style GCSHandler fill:#f0e1ff
    style AzureHandler fill:#e1ffe1
    style HTTPHandler fill:#ffe1f5
    style PVCHandler fill:#f5e1ff
```

## Storage Protocol Detection

```mermaid
flowchart TB
    StorageURI[Storage URI]
    
    subgraph Detection["Protocol Detection"]
        ParseURI[Parse URI]
        ExtractScheme[Extract Scheme]
        
        subgraph Protocols["Supported Protocols"]
            S3[s3 bucket and path]
            GCS[gs bucket and path]
            Azure[https blob.core.windows.net]
            HTTP[http or https server and path]
            PVC[pvc volume-name and path]
        end
        
        ValidateURI{Valid URI?}
    end
    
    subgraph Selection["Handler Selection"]
        SelectS3[S3 Handler]
        SelectGCS[GCS Handler]
        SelectAzure[Azure Handler]
        SelectHTTP[HTTP Handler]
        SelectPVC[PVC Handler]
    end
    
    Error[Return Error]
    
    StorageURI --> ParseURI
    ParseURI --> ExtractScheme
    ExtractScheme --> ValidateURI
    
    ValidateURI -->|s3| SelectS3
    ValidateURI -->|gs| SelectGCS
    ValidateURI -->|azure| SelectAzure
    ValidateURI -->|http or https| SelectHTTP
    ValidateURI -->|pvc| SelectPVC
    ValidateURI -->|Invalid| Error
    
    style Detection fill:#e1f5ff
    style Protocols fill:#fff4e1
    style Selection fill:#f0e1ff
```

## S3 Download Flow

```mermaid
flowchart TB
    Start[S3 URI from s3 bucket and model-path]
    
    subgraph S3Download["S3 Download Process"]
        ParseS3URI[Parse S3 URI<br/>Extract Bucket and Key]
        
        subgraph Authentication["Authentication"]
            CheckCreds{Credentials<br/>Available?}
            EnvCreds[Environment Variables<br/>AWS_ACCESS_KEY_ID]
            SecretCreds[Kubernetes Secret]
            IAMRole[IAM Role for Service Account]
            DefaultCreds[Default Credentials Chain]
        end
        
        subgraph Connection["S3 Connection"]
            CreateClient[Create S3 Client]
            SetEndpoint[Set S3 Endpoint<br/>AWS or MinIO]
            ConfigureRegion[Configure Region]
            SetSSL[SSL and TLS Configuration]
        end
        
        subgraph Transfer["File Transfer"]
            ListObjects[List Objects with Prefix]
            CalculateSize[Calculate Total Size]
            
            subgraph Download["Download Loop"]
                DownloadObject[Download Object]
                ShowProgress[Show Progress]
                VerifyChecksum[Verify MD5/ETag]
                SaveLocal[Save to Local Path]
            end
        end
        
        subgraph PostProcess["Post-processing"]
            ExtractTar[Extract if .tar.gz]
            ValidateFiles[Validate Model Files]
            SetPerms[Set Permissions]
        end
    end
    
    Complete[Download Complete]
    
    Start --> ParseS3URI
    ParseS3URI --> CheckCreds
    
    CheckCreds -->|Check Order| EnvCreds
    EnvCreds --> SecretCreds
    SecretCreds --> IAMRole
    IAMRole --> DefaultCreds
    
    DefaultCreds --> CreateClient
    CreateClient --> SetEndpoint
    SetEndpoint --> ConfigureRegion
    ConfigureRegion --> SetSSL
    
    SetSSL --> ListObjects
    ListObjects --> CalculateSize
    CalculateSize --> DownloadObject
    
    DownloadObject --> ShowProgress
    ShowProgress --> VerifyChecksum
    VerifyChecksum --> SaveLocal
    SaveLocal -->|More Files?| DownloadObject
    
    SaveLocal --> ExtractTar
    ExtractTar --> ValidateFiles
    ValidateFiles --> SetPerms
    SetPerms --> Complete
    
    style S3Download fill:#e1f5ff
    style Authentication fill:#fff4e1
    style Connection fill:#f0e1ff
    style Transfer fill:#e1ffe1
    style PostProcess fill:#ffe1f5
```

## Configuration and Credentials

```mermaid
flowchart TB
    subgraph Config["Storage Configuration"]
        subgraph EnvVars["Environment Variables"]
            StorageURI[STORAGE_URI]
            ModelDir[MODEL_DIR to /mnt/models]
            
            subgraph S3Env["S3 Configuration"]
                S3Endpoint[S3_ENDPOINT]
                S3Region[AWS_REGION]
                S3UseSSL[S3_USE_HTTPS true]
                S3VerifySSL[S3_VERIFY_SSL true]
            end
            
            subgraph GCSEnv["GCS Configuration"]
                GCSProject[GCP_PROJECT]
                GCSCredsPath[GOOGLE_APPLICATION_CREDENTIALS]
            end
            
            subgraph AzureEnv["Azure Configuration"]
                AzureAccount[AZURE_STORAGE_ACCOUNT]
                AzureContainer[AZURE_STORAGE_CONTAINER]
            end
        end
        
        subgraph Secrets["Kubernetes Secrets"]
            S3Secret[S3 Credentials Secret]
            GCSSecret[GCS Service Account Secret]
            AzureSecret[Azure Storage Secret]
            HTTPSecret[HTTP Basic Auth Secret]
        end
        
        subgraph ServiceAccount["Service Account"]
            IRSA[IAM Roles for Service Accounts]
            Workload[Workload Identity GCP]
            ManagedID[Azure Managed Identity]
        end
    end
    
    subgraph Volume["Volume Mounts"]
        ModelVolume[emptyDir model-dir<br/>mountPath /mnt/models]
        SecretVolume[secret volume mounts]
    end
    
    Config --> Volume
    Secrets --> SecretVolume
    ServiceAccount --> Config
    
    style Config fill:#e1f5ff
    style EnvVars fill:#fff4e1
    style Secrets fill:#f0e1ff
    style ServiceAccount fill:#e1ffe1
    style Volume fill:#ffe1f5
```

## Model Validation

```mermaid
flowchart TB
    ModelDownloaded[Model Downloaded]
    
    subgraph Validation["Model Validation"]
        DetectFormat{Detect Model Format}
        
        subgraph Formats["Model Format Validation"]
            ValidateTF[TensorFlow SavedModel<br/>Check saved_model.pb]
            ValidatePyTorch[PyTorch Model<br/>Check .pt or .pth files]
            ValidateSKLearn[SKLearn Model<br/>Check .pkl or .joblib]
            ValidateONNX[ONNX Model<br/>Check .onnx file]
            ValidateHF[HuggingFace Model<br/>Check config.json]
            ValidateCustom[Custom Format]
        end
        
        CheckStructure[Check Directory Structure]
        ValidateMetadata[Validate Metadata Files]
        CheckSize[Check Model Size]
        TestLoad[Test Load Model]
    end
    
    subgraph Result["Validation Result"]
        Success[Validation Success]
        Failure[Validation Failure]
        Retry[Retry Download]
        Fail[Fail Init Container]
    end
    
    ModelDownloaded --> DetectFormat
    
    DetectFormat -->|TensorFlow| ValidateTF
    DetectFormat -->|PyTorch| ValidatePyTorch
    DetectFormat -->|SKLearn| ValidateSKLearn
    DetectFormat -->|ONNX| ValidateONNX
    DetectFormat -->|HuggingFace| ValidateHF
    DetectFormat -->|Unknown| ValidateCustom
    
    ValidateTF --> CheckStructure
    ValidatePyTorch --> CheckStructure
    ValidateSKLearn --> CheckStructure
    ValidateONNX --> CheckStructure
    ValidateHF --> CheckStructure
    ValidateCustom --> CheckStructure
    
    CheckStructure --> ValidateMetadata
    ValidateMetadata --> CheckSize
    CheckSize --> TestLoad
    
    TestLoad -->|Valid| Success
    TestLoad -->|Invalid| Failure
    Failure -->|Retryable| Retry
    Failure -->|Fatal| Fail
    
    style Validation fill:#e1f5ff
    style Formats fill:#fff4e1
    style Result fill:#f0e1ff
```

## Archive Extraction

```mermaid
flowchart TB
    Downloaded[File Downloaded]
    DetectType{File Type?}
    
    subgraph Extraction["Archive Extraction"]
        subgraph ZipExtract["ZIP Extraction"]
            OpenZip[Open ZIP Archive]
            ListZipEntries[List Entries]
            ExtractZipFiles[Extract Files]
        end
        
        subgraph TarExtract["TAR Extraction"]
            OpenTar[Open TAR Archive]
            ListTarEntries[List Entries]
            ExtractTarFiles[Extract Files]
        end
        
        subgraph CompressedExtract["Compressed TAR"]
            Decompress[Decompress gzip/bz2]
            OpenTarGz[Open TAR]
            ExtractCompressed[Extract Files]
        end
        
        SingleFile[Single File<br/>No Extraction]
    end
    
    ValidateExtracted[Validate Extracted Files]
    SetOwnership[Set File Ownership]
    Complete[Extraction Complete]
    
    Downloaded --> DetectType
    
    DetectType -->|.zip| OpenZip
    DetectType -->|.tar| OpenTar
    DetectType -->|.tar.gz/.tgz| Decompress
    DetectType -->|.tar.bz2| Decompress
    DetectType -->|other| SingleFile
    
    OpenZip --> ListZipEntries
    ListZipEntries --> ExtractZipFiles
    
    OpenTar --> ListTarEntries
    ListTarEntries --> ExtractTarFiles
    
    Decompress --> OpenTarGz
    OpenTarGz --> ExtractCompressed
    
    ExtractZipFiles --> ValidateExtracted
    ExtractTarFiles --> ValidateExtracted
    ExtractCompressed --> ValidateExtracted
    SingleFile --> ValidateExtracted
    
    ValidateExtracted --> SetOwnership
    SetOwnership --> Complete
    
    style Extraction fill:#e1f5ff
    style ZipExtract fill:#fff4e1
    style TarExtract fill:#f0e1ff
    style CompressedExtract fill:#e1ffe1
```

## Error Handling and Retry

```mermaid
flowchart TB
    Operation[Storage Operation]
    Error{Error Occurred?}
    
    subgraph ErrorTypes["Error Classification"]
        NetworkError[Network Error<br/>Connection Timeout]
        AuthError[Authentication Error<br/>Invalid Credentials]
        NotFoundError[Not Found Error<br/>Invalid Path]
        PermissionError[Permission Error<br/>Access Denied]
        QuotaError[Quota Error<br/>Rate Limit]
        OtherError[Other Errors]
    end
    
    subgraph RetryLogic["Retry Logic"]
        IsRetryable{Retryable?}
        CheckAttempts{Max Attempts<br/>Reached?}
        ExponentialBackoff[Exponential Backoff<br/>2^attempt * base]
        WaitPeriod[Wait Period]
        RetryOperation[Retry Operation]
    end
    
    subgraph Logging["Error Logging"]
        LogError[Log Error Details]
        RecordMetric[Record Failure Metric]
        EmitEvent[Emit Kubernetes Event]
    end
    
    Success[Operation Success]
    FailInit[Fail Init Container]
    
    Operation --> Error
    Error -->|Yes| ErrorTypes
    Error -->|No| Success
    
    NetworkError --> IsRetryable
    AuthError --> IsRetryable
    NotFoundError --> IsRetryable
    PermissionError --> IsRetryable
    QuotaError --> IsRetryable
    OtherError --> IsRetryable
    
    IsRetryable -->|Yes| CheckAttempts
    IsRetryable -->|No| LogError
    
    CheckAttempts -->|No| ExponentialBackoff
    CheckAttempts -->|Yes| LogError
    
    ExponentialBackoff --> WaitPeriod
    WaitPeriod --> RetryOperation
    RetryOperation --> Operation
    
    LogError --> RecordMetric
    RecordMetric --> EmitEvent
    EmitEvent --> FailInit
    
    style ErrorTypes fill:#ff9999
    style RetryLogic fill:#ffcc99
    style Logging fill:#fff4e1
```

## Performance Optimization

```mermaid
flowchart TB
    subgraph Optimization["Storage Performance Optimization"]
        subgraph Parallelization["Parallel Downloads"]
            MultipleFiles[Multiple Files]
            WorkerPool[Worker Pool]
            ConcurrentDownload[Concurrent Downloads]
            RateLimit[Rate Limiting]
        end
        
        subgraph Caching["Caching Strategy"]
            CheckCache{Model in Cache?}
            UseCache[Use Cached Model]
            DownloadNew[Download New]
            UpdateCache[Update Cache]
        end
        
        subgraph Streaming["Streaming"]
            StreamDownload[Stream Download]
            ChunkedTransfer[Chunked Transfer]
            ProgressiveExtract[Progressive Extraction]
        end
        
        subgraph Compression["Compression"]
            UseCompressed[Download Compressed]
            LocalExtract[Extract Locally]
            SaveBandwidth[Save Bandwidth]
        end
    end
    
    subgraph Monitoring["Download Monitoring"]
        TrackProgress[Track Progress]
        MeasureSpeed[Measure Speed]
        EstimateTime[Estimate Completion]
        LogMetrics[Log Metrics]
    end
    
    Optimization --> Monitoring
    
    style Optimization fill:#e1f5ff
    style Parallelization fill:#fff4e1
    style Caching fill:#f0e1ff
    style Streaming fill:#e1ffe1
    style Compression fill:#ffe1f5
```

## Storage Initializer Container Spec

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: inference-service-pod
spec:
  initContainers:
  - name: storage-initializer
    image: kserve/storage-initializer:v0.11.0
    args:
      - "s3://my-bucket/models/my-model"
      - "/mnt/models"
    env:
      - name: AWS_ACCESS_KEY_ID
        valueFrom:
          secretKeyRef:
            name: s3-credentials
            key: awsAccessKeyID
      - name: AWS_SECRET_ACCESS_KEY
        valueFrom:
          secretKeyRef:
            name: s3-credentials
            key: awsSecretAccessKey
      - name: AWS_REGION
        value: "us-west-2"
      - name: S3_ENDPOINT
        value: "s3.amazonaws.com"
      - name: S3_USE_HTTPS
        value: "true"
      - name: S3_VERIFY_SSL
        value: "true"
    volumeMounts:
      - name: model-dir
        mountPath: /mnt/models
    resources:
      requests:
        cpu: 100m
        memory: 256Mi
      limits:
        cpu: 1
        memory: 1Gi
  
  containers:
  - name: kserve-container
    image: pytorch/torchserve:latest
    volumeMounts:
      - name: model-dir
        mountPath: /mnt/models
        readOnly: true
  
  volumes:
  - name: model-dir
    emptyDir:
      sizeLimit: 10Gi
```

## Multi-Protocol Example

### S3 with IAM Role

```yaml
storageUri: s3://my-bucket/model-path
serviceAccountName: kserve-sa  # Has IAM role attached
```

### GCS with Service Account

```yaml
storageUri: gs://my-bucket/model-path
env:
  - name: GOOGLE_APPLICATION_CREDENTIALS
    value: /var/secrets/google/key.json
volumeMounts:
  - name: gcp-credentials
    mountPath: /var/secrets/google
    readOnly: true
volumes:
  - name: gcp-credentials
    secret:
      secretName: gcp-service-account
```

### Azure Blob Storage

```yaml
storageUri: https://mystorageaccount.blob.core.windows.net/container/model
env:
  - name: AZURE_STORAGE_ACCOUNT
    value: mystorageaccount
  - name: AZURE_STORAGE_KEY
    valueFrom:
      secretKeyRef:
        name: azure-secret
        key: azurestorageaccountkey
```

### HTTP with Authentication

```yaml
storageUri: https://my-server.com/models/my-model.tar.gz
env:
  - name: HTTP_HEADER_AUTHORIZATION
    valueFrom:
      secretKeyRef:
        name: http-secret
        key: authorization
```

### PVC

```yaml
storageUri: pvc://my-pvc/model-directory
volumes:
  - name: model-pvc
    persistentVolumeClaim:
      claimName: my-pvc
```

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Authentication Failed | Missing/invalid credentials | Verify secret configuration |
| Connection Timeout | Network issues | Check endpoint and firewall rules |
| Model Not Found | Incorrect path | Verify storage URI |
| Insufficient Space | Small emptyDir | Increase volume size limit |
| Slow Downloads | Large model | Use compression, parallel downloads |
| Extraction Failed | Corrupted archive | Verify checksums, re-download |

## Best Practices

1. **Use Compressed Archives**: Reduce download time and bandwidth
2. **Implement Checksums**: Verify data integrity
3. **Set Appropriate Timeouts**: Balance reliability and responsiveness
4. **Monitor Download Progress**: Provide visibility into long operations
5. **Cache Models**: Reuse downloaded models when possible
6. **Use IAM Roles**: Avoid credential management when possible
7. **Set Resource Limits**: Prevent resource exhaustion
8. **Enable Retry Logic**: Handle transient failures automatically

## Related Components

- [Data Plane Components](./03-DATA-PLANE-COMPONENTS.md)
- [Predictor Runtime](./05-PREDICTOR-RUNTIME.md)

