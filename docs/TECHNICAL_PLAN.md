# Piano tecnico

## Budget del PC

Hardware di riferimento: Intel i7-10700, RTX 3070 con 8 GB VRAM, 32 GB RAM. L'unita `D:` dispone di circa 1,84 TB liberi.

Budget prudente iniziale:

| Area | Budget |
| --- | ---: |
| Unreal Engine 5.8 e simboli essenziali | 120 GB |
| DDC/Zen e shader | 120 GB |
| Asset Fab/Quixel selezionati | 150 GB |
| Progetto e file intermedi | 200 GB |
| Render EXR/PNG e MP4 | 150 GB |
| Margine libero | oltre 1 TB |

Non scaricare intere librerie. Usare texture 4K per l'ambiente, 8K soltanto per asset molto vicini alla camera e ridurre il pool texture se la VRAM supera 7,5 GB.

## Plugin inclusi nel motore

- Python Editor Script Plugin
- Editor Scripting Utilities
- Sequencer Scripting
- Movie Render Queue / Movie Render Graph
- Water
- Day Sequence (sperimentale, adatto al prototipo)
- Celestial Vault (Beta, scelto per la mappa GlassOrbit)
- Sun Position Calculator come alternativa stabile
- Enhanced Input
- Fab

Il progetto deve usare DirectX 12, Lumen GI/Reflections, Virtual Shadow Maps e Hardware Ray Tracing. Il Path Tracer viene attivato per i render finali, non come viewport abituale.

## Mappa 1: L_GlassOrbit

- Pivot del sistema: `(0, 0, 1000 cm)`.
- Cubo: mesh con bevel reale e spessore, dimensione indicativa 250 cm.
- Moto: rotazione locale continua piu orbita di raggio 700-900 cm intorno al pivot.
- Materiale: vetro solido, IOR circa 1,50, roughness parametrica 0,08-0,22, assorbimento leggermente colorato e micro-normal molto contenuta.
- Cielo: Celestial Vault al World Origin, con Sky Atmosphere, Volumetric Clouds, Sole, Luna, pianeti e sfera stellare astronomica. In viewport usa il catalogo HYG da 10.000 stelle; per gli shot finali puo usare la Via Lattea NASA 8K. Day Sequence rimane la base temporale del sistema.
- LED: istanze emissive con Rect/Point Light; accensione quando il sole scende sotto l'orizzonte, con fade invece di uno scatto netto.
- Camere: free orbit per esplorazione e almeno tre CineCameraActor per reveal, tracking orbitale e close-up delle caustiche/rifrazioni.
- Render: anteprima Lumen 1080p; finale Path Tracer 1440p, con test breve prima di aumentare campioni e rimbalzi.

## Mappa 2: L_OceanLeap

- Base: variante Platforming del Third Person Template con Manny/Quinn.
- Camere: camera su Spring Arm in terza persona e camera in testa/spalla per la prima persona; switch tramite Enhanced Input.
- Blocchi: due piattaforme che ruotano soltanto sull'asse X, senza orbita.
- Oceano: Water Body Ocean, onde Gerstner, normali ad alta frequenza, schiuma e riflessi Lumen Single Layer Water.
- Ambiente: rocce costiere Nanite e materiale sabbia/ciottoli selezionati da Quixel Megascans/Fab.
- Evento salto: trigger di partenza, rilevamento atterraggio sul secondo blocco e shot esterno in Sequencer al tramonto. Per il primo test l'azione e deterministica e ripetibile.
- Render: Lumen Hardware Ray Tracing per acqua e personaggio animato; Path Tracer valutato soltanto per singoli hero shot.

## Asset gratuiti selezionati

Prima scelta, senza download aggiuntivi:

- Manny e Quinn dal Third Person Template.
- Water plugin e onde Gerstner integrate.
- Sky Atmosphere, Volumetric Clouds e Day Sequence integrati.
- Primitive e Modeling Mode per i blocchi e il cubo bevelled.

Scelta Fab/Quixel da aggiungere solo alla seconda mappa:

- Nordic Beach Rock Formation.
- Nordic Coastal Cliff o Massive Nordic Coastal Cliff, uno solo dopo confronto visivo.
- Beach Sand With Pebbles.
- Eventuale Beach Boulder per dettaglio in primo piano.

Per il vetro viene acquisito anche `JVAD3D PRO GLASS A (Free)`: e un pacchetto Lumen da circa 100 MB con 30 esempi. Serve come riferimento e anteprima; il materiale finale del cubo resta personalizzato per avere spessore, IOR e assorbimento corretti nel Path Tracer.

Per un tramonto statico di riferimento si puo usare `Belfast Sunset (Pure Sky)` di Poly Haven in versione 4K/8K CC0. Non va usato come sorgente principale del ciclo giorno/notte per evitare luce e sole incoerenti.

## Decisione sul sistema oceanico

Ordine di prova, senza acquistare asset alla cieca:

1. Water plugin integrato: baseline gratuita con Water Body Ocean e onde Gerstner.
2. Easy Waterscape: prima alternativa commerciale per gli shot oceanici. Offre FFT Tessendorf/JONSWAP, oceano infinito, CoastMaker, foam, buoyancy ed e compatibile con UE 5.7+ e Movie Render Queue.
3. Dynamic Real Water: alternativa se il progetto richiede fisica, interazioni, scie, galleggiamento e gameplay avanzato. E un plugin C++ giovane ma dichiara circa 2,7 ms su RTX 3060 Ti.
4. Fluid Flux: da usare solo se aggiungiamo fiumi, cascate o acqua bassa che scorre sul terreno. Non e la scelta principale per l'oceano: la simulazione e una griglia 2D su heightfield, non supporta open world, non simula la rottura delle onde e non si integra con il Water plugin.
5. Fluid Ninja LIVE: complemento futuro per spruzzi e VFX locali; non sostituisce l'oceano e richiede un periodo di apprendimento.
6. Oceanology NextGen: escluso dal primo test. Il produttore indica RTX 3080/RTX 4070+ mentre il PC usa RTX 3070.

La scelta consigliata e iniziare gratis con Water. Se il confronto visivo non basta, acquistare al massimo Easy Waterscape, dopo aver verificato prezzo, licenza e demo con l'account Fab.

## Output web

GitHub Pages ospitera una galleria statica, non l'applicazione Unreal. Ogni clip deve restare sotto 100 MiB e idealmente tra 10 e 35 MiB:

- MP4 H.264, `yuv420p`, 1080p, CRF 18-22, `faststart`.
- Poster WebP/JPEG per evitare autoplay pesante.
- Versione WebM opzionale soltanto se porta un reale risparmio.

Git LFS non e adatto agli asset serviti da GitHub Pages. I frame EXR/PNG, i file Unreal e gli asset sorgente restano locali; sul repository vanno solo sito, poster e clip compresse.
