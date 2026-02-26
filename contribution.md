# Como contribuir

Este guia explica o fluxo de trabalho para contribuir com um dos projetos do repositório. O TinyDB será usado como exemplo, mas o processo é idêntico para `python-dotenv` e `whoosh-reloaded`.

---

## 1. Clonar o repositório com os submódulos

```bash
git clone --recurse-submodules https://github.com/matheusvir/eda-oss-performance.git
cd eda-oss-performance
```

O `--recurse-submodules` garante que as pastas `tinydb`, `python-dotenv` e `whoosh-reloaded` sejam preenchidas. Sem ele, essas pastas ficam vazias.

---

## 2. Entrar no submódulo e criar uma branch

```bash
cd tinydb
git checkout -b minha-otimizacao
```

O submódulo é um repositório git independente que aponta para o fork `matheusvir/tinydb`. Todo commit e push feito dentro dessa pasta vai direto para esse fork.

---

## 3. Fazer as alterações, commitar e pushear

```bash
# dentro de tinydb/
git add .
git commit -m "descrição da otimização"
git push origin minha-otimizacao
```

---

## 4. Abrir o Pull Request

Abra o PR no GitHub com a seguinte direção:

- **origem:** `matheusvir/tinydb` → branch `minha-otimizacao`
- **destino:** `msiemens/tinydb` → branch `master`

---

## 5. Atualizar a referência no repositório principal

O repositório pai (`eda-oss-performance`) registra um ponteiro para um commit específico de cada submódulo. Após avançar no submódulo, atualize esse ponteiro:

```bash
# na raiz do eda-oss-performance
cd ..
git add tinydb
git commit -m "update tinydb submodule"
git push origin main
```

---

## Observação

O submódulo sempre aponta para um commit específico, não para uma branch. Por isso o passo 5 deve ser executado sempre que houver avanço no submódulo que precise ser registrado no repositório principal.
