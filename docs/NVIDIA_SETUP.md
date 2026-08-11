# NVIDIA per Orbital Glass Lab

## Stato verificato l'11 agosto 2026

- GPU: NVIDIA GeForce RTX 3070, 8 GB.
- Driver ancora installato: 560.94.
- Software presente: GeForce Experience 3.28.0.417 (obsoleto).
- NVIDIA App e Nsight Graphics non sono ancora installati.
- Installer ufficiale preparato: `D:\UnrealInstallers\NVIDIA\NVIDIA_app_v11.0.8.299.exe`.
- SHA-256: `DF54C76346A8C4B3D9CC2D65B31D92E68BC0FEF73BA0A775DDB53264D7EE75D6`.
- Firma Authenticode verificata: valida, NVIDIA Corporation.

L'installazione non e partita perche Windows ha richiesto la conferma UAC. Serve essere davanti al PC; non serve effettuare il login NVIDIA per installare l'app o il driver.

## Quando si torna davanti al PC

1. Avviare `D:\UnrealInstallers\NVIDIA\NVIDIA_app_v11.0.8.299.exe` e confermare UAC.
2. Aprire NVIDIA App, scheda Driver, selezionare **Studio Driver** e installare la versione proposta.
3. Riavviare Windows se richiesto.
4. Impostare come cartella delle catture `D:\UnrealRenders\OrbitalGlassLab\Captures`.
5. Per le clip usare HEVC/H.265 oppure H.264: RTX 3070 non dispone dell'encoder AV1 delle RTX 40 e successive.

Verifica rapida dopo il riavvio:

```powershell
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
```

## Tool NVIDIA scelti

- **NVIDIA App**: driver Studio, overlay prestazioni e ShadowPlay per registrare viewport o build Unreal.
- **Nsight Graphics**: installarlo in seguito, quando il progetto Unreal funziona, per analizzare frame DirectX 12, ray tracing, shader e colli di bottiglia GPU.

## Tool da non installare adesso

- **Project G-Assist**: la RTX 3070 e compatibile, ma su 8 GB richiede gran parte della VRAM libera; entrerebbe in conflitto con Unreal, Lumen, vetro e oceano.
- **Omniverse Connector for Unreal**: il connettore ufficiale si ferma a Unreal 5.3; per UE 5.8 useremo il supporto USD nativo di Epic se necessario.
- **RTX Remix**: pensato per rimasterizzare giochi classici, non per costruire questa scena.
- **NVIDIA Broadcast**: utile per microfono/webcam, non per rendering e riprese in-engine.

GeForce NOW non sostituisce una workstation Unreal e non serve per ospitare il progetto. Le clip finali MP4 potranno essere pubblicate normalmente su GitHub Pages; il rendering restera locale.
