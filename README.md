# Allgemein
Streamlit App für das Gruppenprojekt in PKI. Teilnehmer: Zekiye Saylam, Björn Schmidt, Sascha Zhu, Daniel Owona

Das Ergebnis ist die Webapp unter: https://owonadan-pki-interaktive-karten-app-ge8krp.streamlit.app/

# Environment Setup
## Clonen von Github
1. In das Verzeichnis wechseln, wohin das Projekt von github gecloned werden soll.
2. Kommando ausführen  
```git clone https://github.com/owonadan/PKI-Interaktive-Karten```

## Installation mit Anaconda/Miniconda
1. in das Verzeichnis PKI-Interaktive-Karten wechseln
2. Dort folgende Befehle ausführen:  
```
conda env create -f ./environment/environment.yaml
conda activate PKI
```

# Input Dateien für Streamlit App lokal erzeugen
**Hinweis**: An dieser Stelle wird der Vollständigkeit halber exemplarisch beschrieben, 
wie man die .csv Dateien, die von der Streamlit App genutzt werden, 
lokal erzeugen kann.

Die Streamlit App bedient sich aus den beiden .csv Dateien, 
die im Verzeichnis /data in diesem Repository liegen. 
Diese können zum aktuellen Stand nur von den Projektgruppenteilnehmern in diesem Repository aktualisiert werden.
```
python hoflaeden_async.py
python unverpackt_async.py
```
