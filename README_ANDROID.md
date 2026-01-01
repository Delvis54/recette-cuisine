But de ce fichier

Ce dossier contient une application Kivy 'Recettes' et une configuration pour générer
un fichier APK (Android) via Buildozer.

Comment obtenir directement l'APK (méthode recommandée - automatisée):
1. Créez un dépôt GitHub et poussez ce projet (toutes modifications que vous souhaitez).
2. Sur GitHub, allez dans l'onglet Actions: la workflow "Build Android APK" se déclenchera sur le push vers `main` ou `master`.
3. Une fois le workflow terminé, vous trouverez l'artefact nommé `recettes-apk` dans la page du workflow (Download).

Remarques importantes:
- L'APK produit est un build de débogage (unsigned). Il est utilisable pour l'installation directe (sideload) sur votre appareil Android.
- Pour publier sur le Play Store, il faudra signer correctement l'APK/Bundle et configurer les clés.

Comment builder localement (WSL / Ubuntu) :
1. Installez WSL 2 + Ubuntu et ouvrez un terminal Ubuntu dans le dossier du projet.
2. Installez dépendances :
   sudo apt update; sudo apt install -y python3-pip build-essential git zip openjdk-8-jdk zlib1g-dev libncurses5 libncurses5-dev libstdc++6 libffi-dev libssl-dev liblzma-dev libbz2-dev libreadline-dev libsqlite3-dev libjpeg-dev libfreetype6-dev
3. Pip et Buildozer :
   python3 -m pip install --upgrade pip
   pip install buildozer cython
4. Lancez la build :
   buildozer android debug

Si vous voulez, je peux :
- Aider à pousser ce projet vers GitHub et configurer le workflow.
- Ou vous guider pas à pas pour builder l'APK localement sur WSL.

Si vous voulez que je génère effectivement l'APK pour vous, fournissez un accès au dépôt GitHub (ou permettez-moi d'appuyer/fermer une PR) — je peux préparer tout et déclencher le build CI pour que vous téléchargiez l'artefact.
