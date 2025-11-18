#!/usr/bin/env python3
import os
import re
from pathlib import Path

print("🔍 ANALYSE COMPLÈTE NEOBOT\n")

# 1. Vérifier la structure
print("📁 STRUCTURE DU PROJET:")
for root, dirs, files in os.walk('.', topdown=True):
    dirs[:] = [d for d in dirs if d not in ['node_modules', '__pycache__', 'venv', '.next', 'auth_info_baileys']]
    level = root.replace('.', '').count(os.sep)
    indent = ' ' * 2 * level
    print(f"{indent}{os.path.basename(root)}/")
    subindent = ' ' * 2 * (level + 1)
    for file in files[:5]:  # Limite à 5 fichiers par dossier
        print(f"{subindent}{file}")

print("\n" + "="*50)

# 2. Analyser backend/.env
print("\n🔑 ANALYSE .env:")
env_path = Path('backend/.env')
if env_path.exists():
    env_content = env_path.read_text()
    
    # Chercher doublons
    keys = re.findall(r'^(\w+)=', env_content, re.MULTILINE)
    duplicates = [k for k in set(keys) if keys.count(k) > 1]
    
    if duplicates:
        print(f"❌ Clés dupliquées: {duplicates}")
    else:
        print("✅ Pas de doublons")
    
    # Vérifier ENCRYPTION_KEY
    enc_keys = re.findall(r'ENCRYPTION_KEY=(.+)', env_content)
    if len(enc_keys) > 1:
        print(f"❌ {len(enc_keys)} ENCRYPTION_KEY trouvées!")
    elif enc_keys:
        print(f"✅ ENCRYPTION_KEY présente")
else:
    print("❌ Fichier .env absent")

print("\n" + "="*50)

# 3. Analyser models.py
print("\n📊 ANALYSE models.py:")
models_path = Path('backend/app/models.py')
if models_path.exists():
    models_content = models_path.read_text()
    
    # Chercher classes dupliquées
    classes = re.findall(r'class (\w+)\(', models_content)
    duplicates = [c for c in set(classes) if classes.count(c) > 1]
    
    if duplicates:
        print(f"❌ Classes dupliquées: {duplicates}")
    else:
        print(f"✅ Pas de doublons ({len(set(classes))} classes)")
else:
    print("❌ models.py absent")

print("\n" + "="*50)

# 4. Analyser main.py
print("\n🚀 ANALYSE main.py:")
main_path = Path('backend/app/main.py')
if main_path.exists():
    main_content = main_path.read_text()
    
    # Chercher routes dupliquées
    routes = re.findall(r'@app\.(get|post|put|delete)\("([^"]+)"\)', main_content)
    route_paths = [r[1] for r in routes]
    duplicates = [r for r in set(route_paths) if route_paths.count(r) > 1]
    
    if duplicates:
        print(f"❌ Routes dupliquées: {duplicates}")
    else:
        print(f"✅ Pas de doublons ({len(routes)} routes)")
    
    # Imports
    imports = re.findall(r'^from .* import', main_content, re.MULTILINE)
    print(f"📦 {len(imports)} imports trouvés")
else:
    print("❌ main.py absent")

print("\n" + "="*50)

# 5. Vérifier Docker
print("\n🐳 ANALYSE DOCKER:")
import subprocess
try:
    result = subprocess.run(['docker', 'ps', '-a'], capture_output=True, text=True)
    postgres_containers = [line for line in result.stdout.split('\n') if 'postgres' in line.lower()]
    
    if postgres_containers:
        print(f"✅ {len(postgres_containers)} container(s) PostgreSQL:")
        for container in postgres_containers:
            print(f"   {container[:80]}")
    else:
        print("❌ Aucun container PostgreSQL")
except:
    print("❌ Docker non disponible")

print("\n" + "="*50 + "\n")
