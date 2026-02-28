# Como contribuir

Este documento descreve os fluxos de trabalho do projeto. Cada atividade pertence a um de quatro tipos: **Implementação**, **Validação**, **Performance** ou **Utilitários**.

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

# 2. Criar uma branch descritiva para a otimização
git checkout -b otimizacao/nome-da-otimizacao

# 3. Realizar as alterações no código

# 4. Commitar e pushear para o fork
git add .
git commit -m "descrição objetiva da otimização"
git push origin otimizacao/nome-da-otimizacao

# 5. Abrir Pull Request no GitHub
# origem:  matheusvir/tinydb → optimization/nome-da-otimizacao(use inglês para o nome da otimização)
# destino: matheusvir/tinydb → main  (branch principal do fork)
```

O PR é aberto **dentro do fork** para revisão interna da equipe. O repositório original só será atualizado ao final do projeto, após todas as validações.

**Após o PR ser aprovado internamente**, atualizar o ponteiro do submódulo no repositório principal:

```bash
# na raiz do eda-oss-performance
cd ..
git add tinydb
git commit -m "update tinydb submodule"
git push origin main
```

---

### 2. Validação

O membro responsável revisa o código de uma otimização e aprova ou solicita ajustes no PR aberto dentro do submódulo.

**Critérios de aprovação:**

- O comportamento original do projeto foi mantido (testes existentes continuam passando)
- O código está legível e bem documentado
- A lógica da otimização está clara e justificada
- Não há regressões introduzidas

**Fluxo:**

1. Acessar o PR aberto no fork correspondente (ex: `github.com/matheusvir/tinydb/pulls`)
2. Revisar as alterações na aba **Files changed**
3. Executar localmente se necessário:

```bash
cd tinydb
git fetch origin
git checkout otimizacao/nome-da-otimizacao

# rodar os testes do projeto
pip install -e .
pytest
```

4. Aprovar o PR ou solicitar mudanças com comentários objetivos

---

### 3. Performance

O membro responsável mede o impacto real da otimização utilizando um ambiente Docker isolado, garantindo que os resultados tenham validade estatística.

**Ambiente:** Docker (definido em `setup/<projeto>/`). Todos os experimentos devem ser executados dentro deste ambiente para garantir reprodutibilidade.

**Fluxo:**

```bash
# 1. Subir o ambiente Docker do projeto
cd setup/tinydb
docker build -t eda-tinydb .
docker run --rm -v $(pwd)/../../experiments/tinydb:/experiments \
                -v $(pwd)/../../results/tinydb:/results \
                eda-tinydb
```

O script de experimento deve salvar os resultados em `/results`, que serão persistidos em `results/tinydb/` no repositório.

**Critérios de validação estatística:**

- Executar o experimento no mínimo **30 vezes** para garantir significância
- Calcular **média** e **desvio padrão** antes e depois da otimização
- A melhora é considerada comprovada quando a média pós-otimização supera a média anterior por uma margem maior que um desvio padrão

**Formato dos resultados** (`results/<projeto>/nome-do-experimento.json`):

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

# Criar uma branch descritiva
git checkout -b util/nome-da-tarefa

# Realizar as alterações
git add .
git commit -m "descrição da tarefa"
git push origin util/nome-da-tarefa

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
| Implementação | Dentro do submódulo | `otimizacao/nome` no fork | Branch `main` do fork (revisão interna) |
| Validação | Revisão no GitHub | — | Aprovação no fork |
| Performance | `experiments/` + Docker | `main` do repositório principal | — |
| Utilitários | Raiz do repositório principal | `util/nome` | `main` do repositório principal |
| Envio ao upstream | Dentro do submódulo | `main` do fork | Repositório original (fim do projeto) |
