# Como contribuir

Este documento descreve os fluxos de trabalho do projeto. Cada atividade pertence a um de quatro tipos: **Implementação**, **Validação**, **Performance** ou **Utilitários**.

---

## Padrões gerais

### Idioma

Todos os commits, nomes de branch e comentários de código devem ser escritos em **inglês**.

### Convenção de commits

Os commits devem seguir o padrão [Conventional Commits](https://www.conventionalcommits.org):

```
<tipo>(<escopo>): <descrição curta>
```

**Tipos disponíveis:**

| Tipo | Quando usar |
|---|---|
| `feat` | Adição de nova funcionalidade ou otimização |
| `fix` | Correção de bug ou comportamento incorreto |
| `refactor` | Refatoração de código sem mudança de comportamento |
| `perf` | Mudança com foco exclusivo em performance |
| `test` | Adição ou correção de testes |
| `docs` | Alterações em documentação |
| `chore` | Tarefas de manutenção (dependências, configurações) |

**Exemplos:**

```bash
feat(tinydb): implement b-tree index for document lookup
fix(tinydb): correct bloom filter false positive rate
perf(python-dotenv): replace dict merge with chainmap
test(whoosh): add stress test for negative lookups
docs: update contribution workflow
```

O **escopo** é opcional mas recomendado — use o nome do projeto (`tinydb`, `python-dotenv`, `whoosh`).

### Nomenclatura de branches

Use sempre **inglês** e o prefixo adequado ao tipo de trabalho:

| Prefixo | Uso |
|---|---|
| `optimization/` | Implementação de otimização nos forks |
| `fix/` | Correção de bug nos forks |
| `util/` | Tarefas utilitárias no repositório principal |

**Exemplos:**

```
optimization/bloom-filter-negative-lookup
optimization/btree-document-index
fix/chainmap-interpolation-edge-case
util/docker-setup
util/final-report
```

---

### Padrão de Pull Request

Todo PR aberto (tanto nos forks quanto no repositório principal) deve seguir o formato abaixo no título e na descrição.

**Título:**

```
<tipo>(<escopo>): <descrição curta>
```

Seguindo a mesma convenção de commits. Exemplos:

```
feat(tinydb): implement b-tree index for document lookup
perf(python-dotenv): replace dict merge with chainmap
chore: add docker setup for all projects
```

**Descrição (corpo do PR):**

```markdown
## O que foi feito
Descrição objetiva da mudança implementada e a motivação por trás dela.

## Como testar
Passos para reproduzir e verificar o comportamento localmente.

## Issue relacionada
Closes #<número>
```

---

### Nomenclatura de arquivos

Use sempre **inglês** e o prefixo adequado ao tipo de conteúdo:

| Prefixo | Tipo | Localização | Exemplo |
|---|---|---|---|
| `baseline_` | Script de medição antes da otimização | `experiments/<projeto>/` | `baseline_tinydb_btree.py` |
| `experiment_` | Script de medição após a otimização | `experiments/<projeto>/` | `experiment_tinydb_btree.py` |
| `result_` | Resultado JSON de um experimento | `results/<projeto>/` | `result_tinydb_btree.json` |
| `Dockerfile` | Ambiente isolado do projeto | `setup/<projeto>/` | `Dockerfile` |

O `<otimizacao>` no nome do arquivo deve corresponder à branch de implementação, sem o prefixo `optimization/`. Exemplos:

```
experiments/tinydb/baseline_tinydb_btree.py
experiments/tinydb/experiment_tinydb_btree.py
results/tinydb/result_tinydb_btree.json

experiments/python-dotenv/baseline_python-dotenv_chainmap.py
experiments/python-dotenv/experiment_python-dotenv_chainmap.py
results/python-dotenv/result_python-dotenv_chainmap.json
```

---

## Estrutura do repositório

```
eda-oss-performance/
├── experiments/
│   ├── tinydb/
│   ├── python-dotenv/
│   └── whoosh-reloaded/
├── setup/
│   ├── tinydb/
│   ├── python-dotenv/
│   └── whoosh-reloaded/
├── results/
│   ├── tinydb/
│   ├── python-dotenv/
│   └── whoosh-reloaded/
├── tinydb/              # submódulo — fork do projeto original
├── python-dotenv/       # submódulo — fork do projeto original
└── whoosh-reloaded/     # submódulo — fork do projeto original
```

| Pasta | Conteúdo |
|---|---|
| `experiments/<projeto>/` | Scripts que executam os testes de carga |
| `setup/<projeto>/` | Dockerfile e instruções do ambiente isolado |
| `results/<projeto>/` | Arquivos `.json` gerados pelos experimentos |

---

## Tipos de atividade

### 1. Implementação

O membro responsável realiza uma otimização dentro do submódulo do projeto.

**Pré-requisitos:** ter clonado o repositório com submódulos.

```bash
git clone --recurse-submodules https://github.com/matheusvir/eda-oss-performance.git
cd eda-oss-performance
```

Se o repositório já foi clonado sem submódulos:

```bash
git submodule update --init --recursive
```

**Fluxo:**

```bash
# 1. Entrar no submódulo do projeto
cd tinydb  # ou python-dotenv / whoosh-reloaded

# 2. Criar uma branch descritiva para a otimização (em inglês)
git checkout -b optimization/btree-document-index

# 3. Realizar as alterações no código

# 4. Commitar seguindo a convenção de commits (em inglês)
git add .
git commit -m "feat(tinydb): implement b-tree index for document lookup"
git push origin optimization/btree-document-index

# 5. Abrir Pull Request no GitHub
# origem:  matheusvir/tinydb → optimization/btree-document-index
# destino: matheusvir/tinydb → main  (branch principal do fork)
```

O PR é aberto **dentro do fork** para revisão interna da equipe. O repositório original só será atualizado ao final do projeto, após todas as validações.

> **Nota:** A atualização do ponteiro do submódulo no repositório principal é de **responsabilidade exclusiva do owner do projeto** (matheusvir) após o merge do PR.

---

### Isolamento de implementações para testes de performance

**Importante:** Quando um projeto possui múltiplas otimizações em desenvolvimento simultâneo, é essencial **isolar cada implementação** antes de executar os testes de performance. Isso garante que os resultados reflitam exclusivamente o impacto da otimização sendo medida, sem interferência de outras mudanças não relacionadas.

**Cenário típico:**

Imagine que o projeto `tinydb` possui três otimizações em andamento:

- `optimization/btree-document-index` (branch A)
- `optimization/bloom-filter-negative-lookup` (branch B)
- `optimization/cache-layer` (branch C)

Ao testar o desempenho da otimização B (bloom filter), é necessário garantir que o código testado contém **somente** a implementação do bloom filter, e não inclui as mudanças das branches A ou C.

**Como isolar uma implementação:**

```bash
# 1. Entrar no submódulo do projeto
cd tinydb

# 2. Garantir que você está partindo da branch principal limpa
git checkout main
git pull origin main

# 3. Fazer checkout da branch da otimização que você deseja testar
git checkout optimization/bloom-filter-negative-lookup

# 4. Verificar que não há outras mudanças mescladas indevidamente
git log --oneline main..HEAD
# Deve aparecer apenas os commits da otimização sendo testada

# 5. Executar os testes de performance SOMENTE nesta branch isolada
cd ..
bash experiments/tinydb/run_bloom-filter-negative-lookup.sh
```

**O que evitar:**

- **Não** mescle múltiplas branches de otimização antes de testar
- **Não** execute testes a partir da `main` se ela já contém outras otimizações mergeadas
- **Não** assuma que o código está isolado sem verificar o histórico de commits

**Estratégia recomendada:**

Caso a branch `main` do fork já contenha outras otimizações mergeadas e você precise isolar apenas uma delas para re-testar:

```bash
# Criar uma branch temporária a partir do commit anterior às otimizações
git checkout main
git log --oneline  # identificar o último commit antes das otimizações

# Criar branch de teste isolada
git checkout -b temp-isolated-test <commit-hash>
git cherry-pick <commit-da-otimizacao-desejada>

# Agora você tem uma branch com APENAS a otimização isolada
```

---

### 2. Validação

O membro responsável revisa o código de uma otimização, executa os testes e reporta o resultado no canal de comunicação oficial da equipe.

**Critérios de aprovação:**

- O comportamento original do projeto foi mantido (testes existentes continuam passando)
- O código está legível e bem documentado
- A lógica da otimização está clara e justificada
- Não há regressões introduzidas

**Fluxo:**

1. Acessar o PR aberto no fork correspondente (ex: `github.com/matheusvir/tinydb/pulls`)
2. Revisar as alterações na aba **Files changed**
3. Executar localmente:

```bash
cd tinydb
git fetch origin
git checkout optimization/btree-document-index

# rodar os testes do projeto
pip install -e .
pytest
```

4. Reportar o resultado no canal de comunicação oficial da equipe com:
   - Status dos testes (passou / falhou)
   - Observações sobre o código revisado
   - Aprovação ou lista de ajustes necessários

---

### 3. Performance

O membro responsável mede o impacto real da otimização utilizando um ambiente Docker isolado, garantindo que os resultados tenham validade estatística.

> **Lembre-se:** Sempre execute os testes de performance em uma branch isolada contendo **apenas** a otimização sendo medida. Consulte a seção "Isolamento de implementações para testes de performance" acima.

**Ambiente:** Docker (definido em `setup/<projeto>/`). Todos os experimentos devem ser executados dentro deste ambiente para garantir reprodutibilidade.

**Fluxo:**

```bash
# Na raiz do repositório principal
git checkout main
git checkout -b perf/<projeto>-<otimizacao>

# Criar os scripts de benchmark em experiments/<projeto>/
# e executar via script de run dentro do Docker
bash experiments/<projeto>/run_<otimizacao>.sh

# Commitar scripts e resultado JSON
git add experiments/<projeto>/ results/<projeto>/
git commit -m "perf(<projeto>): add benchmark scripts for <otimizacao>"
git push origin perf/<projeto>-<otimizacao>

# Abrir PR para a main no repositório eda-oss-performance
```

> Os scripts de benchmark só devem ser abertos em PR após a otimização correspondente estar implementada e o experimento ter rodado com pelo menos 30 execuções.

**Critérios de validação estatística:**

- Executar o experimento no mínimo **30 vezes** para garantir significância
- Calcular **média** e **desvio padrão** antes e depois da otimização
- A melhora é considerada comprovada quando a média pós-otimização supera a média anterior por uma margem maior que um desvio padrão

**Formato dos resultados** (`results/<projeto>/result_<projeto>_<otimizacao>.json`):

```json
{
  "experiment": "nome-da-otimizacao",
  "project": "tinydb",
  "baseline": {
    "mean_ms": 0.0,
    "std_ms": 0.0,
    "runs": 30
  },
  "optimized": {
    "mean_ms": 0.0,
    "std_ms": 0.0,
    "runs": 30
  },
  "improvement_pct": 0.0
}
```

Se a melhora for comprovada estatisticamente, a otimização está pronta. O envio ao repositório oficial ocorre na etapa final do projeto, descrita abaixo.

---

### 4. Utilitários

Atividades de suporte ao projeto: ambiente Docker, relatórios, gráficos, README e documentação.

**Exemplos de tarefas:**

- Criar ou atualizar o `Dockerfile` em `setup/<projeto>/`
- Escrever ou atualizar o `README.md`
- Gerar gráficos comparativos a partir dos JSONs em `results/`
- Redigir o relatório final do projeto
- Realizar workshop de Git/GitHub para a equipe

**Fluxo:**

```bash
# Na raiz do repositório principal (não dentro de um submódulo)
git checkout main

# Criar uma branch descritiva (em inglês)
git checkout -b util/docker-setup

# Realizar as alterações
git add .
git commit -m "chore: add docker setup for all projects"
git push origin util/docker-setup

# Abrir PR para a main no repositório eda-oss-performance
```

---

## 5. Envio ao repositório oficial

Esta etapa ocorre **somente ao fim do projeto**, após todas as otimizações terem sido aprovadas internamente (Validação) e comprovadas em termos de performance (Performance).

```bash
# Dentro do submódulo
cd tinydb

# A partir da branch principal do fork, abrir PR para o repositório original
# origem:  matheusvir/tinydb → main
# destino: msiemens/tinydb  → master
```

O PR é aberto no GitHub apontando do fork para o repositório **original**.

---

## Resumo

| Tipo | Onde trabalha | Branch | PR para |
|---|---|---|---|
| Implementação | Dentro do submódulo | `optimization/name` no fork | Branch `main` do fork (revisão interna) |
| Validação | Revisão local + report no canal da equipe | — | — |
| Performance | `experiments/` + Docker | `perf/<projeto>-<otimizacao>` | `main` do repositório principal (após experimento completo) |
| Utilitários | Raiz do repositório principal | `util/nome` | `main` do repositório principal |
| Envio ao upstream | Dentro do submódulo | `main` do fork | Repositório original (fim do projeto) |
