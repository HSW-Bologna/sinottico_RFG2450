
# Sinottico per Telemetria e Collaudo di Dispositivi RFG2450

Modulo Python implementante una semplice interfaccia grafica per il collaudo di dispositivi RFG2450.

# Requisiti

Le dipendenze sono elencate nel file `requirements.txt`. Le piu' notabili sono `PySimpleGUI`, `pyserial` e `algebraic-data-types`; tutte le altre dovrebbero essere dipendenti da queste o gia' incluse in una tipica installazione di Python. `pyinstaller` e' necessario solo per pacchettizzare un eseguibile.

# Installazione

Una volta scaricata la repository, il programma puo' essere eseguito lanciando lo script `main.py`. Per pacchettizzare un eseguibile compatibile con la piattaforma che si sta correntemente usando, invocare il comando `pyinstaller sinottico.spec`.

# TODO

    - Gestire tutte le possibili eccezioni (Per esempio nella procedura automatica se arriva un messaggio malformato)
    - Raccogliere tutte le variabili in delle strutture
    - Smettere di usare implicitamente '\r\n' come fine riga, sfruttare l'opzione configurata
    - Riunire i popup in un unico file