# Sinottico per Telemetria e Collaudo di Dispositivi RFG2450

Modulo Python implementante una semplice interfaccia grafica per il collaudo di dispositivi RFG2450.

# Requisiti

Le dipendenze sono elencate nel file `requirements.txt`. Le piu' notabili sono `PySimpleGUI`, `pyserial` e `algebraic-data-types`; tutte le altre dovrebbero essere dipendenti da queste o gia' incluse in una tipica installazione di Python. `pyinstaller` e' necessario solo per pacchettizzare un eseguibile.

# Installazione

Una volta scaricata la repository, il programma puo' essere eseguito lanciando lo script `main.py`. Per pacchettizzare un eseguibile compatibile con la piattaforma che si sta correntemente usando, invocare il comando `pyinstaller sinottico.spec`.

# TODO

    - Raccogliere tutte le variabili in delle strutture
    - Aggiungere la funzione della tab di calibrazione: apri un foglio di Excel, estrai i dati letti e genera le possibili combinazioni dei parametri A, B, C, D; calcola poi il delta tra le funzioni registrate e calcolate; organizza i risultati in ordine, mostrando i primi 10 piu' corretti
    - Disegnare un gauge per la potenza per la prima tab
    - Usa il Pane anziche' le tab
