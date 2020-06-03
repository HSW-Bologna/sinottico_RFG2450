
# Sinottico per Telemetria e Collaudo di Dispositivi RFG2450

Modulo Python implementante una semplice interfaccia grafica per il collaudo di dispositivi RFG2450.

# Requisiti

Le dipendenze sono elencate nel file `requirements.txt`. Le piu' notabili sono `PySimpleGUI`, `pyserial` e `algebraic-data-types`; tutte le altre dovrebbero essere dipendenti da queste o gia' incluse in una tipica installazione di Python. `pyinstaller` e' necessario solo per pacchettizzare un eseguibile.

# Installazione

Una volta scaricata la repository, il programma puo' essere eseguito lanciando lo script `main.py`. Per pacchettizzare un eseguibile compatibile con la piattaforma che si sta correntemente usando, invocare il comando `pyinstaller sinottico.spec`.

# TODO

 - Connettere la seriale per la prima volta e non richiederlo piu'
 - Disabilitare le Tab quando la seriale non e' connessa
 - Non inviare messaggi periodici/automatici