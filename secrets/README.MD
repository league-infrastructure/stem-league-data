# Secrets


## Tasks

  inv secrets-edit prod           Edit secrets/prod.env in place
  
  inv secrets-encrypt             Encrypt using DEPLOYMENT from current .env
  
  inv secrets-updatekeys dev      Re-encrypt after .sops.yaml changes
  inv secrets-updatekeys prod     Re-encrypt after .sops.yaml changes

## Workflow Example:

  1. Decrypt dev secrets:
     inv decrypt dev
     (creates .env with DEPLOYMENT=dev)
  
  2. Make changes to .env:
     edit .env
  
  3. Encrypt back to secrets/dev.env:
     inv encrypt
     (reads DEPLOYMENT=dev from .env)
  
  4. Switch to prod secrets:
     inv decrypt prod
     (overwrites .env with DEPLOYMENT=prod)
  
  5. Edit prod secrets:
     inv secrets-edit prod
     (SOPS decrypts, opens in editor, re-encrypts)

