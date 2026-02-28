# Tasks do Projeto — EDA OSS Performance
# Este arquivo NÃO deve ser commitado (.gitignore)

## Legenda de tipos
# [IMP] Implementação
# [VAL] Validação
# [PERF] Performance
# [UTIL] Utilitários

---

## UTILITÁRIOS

- [ ] [UTIL] Criar ambiente Docker padrão para os 3 projetos
      Responsável: João Pereira
      Descrição: Criar o Dockerfile base em setup/ que será usado nos experimentos
                 de performance dos 3 projetos. Garantir isolamento e reprodutibilidade.

- [ ] [UTIL] Escrever o README.md
      Responsável: Matheus Virgolino
      Descrição: Redigir a primeira versão do README, delimitando as otimizações
                 propostas, o ambiente de teste e os benchmarks definidos.
      Issue: #1

- [ ] [UTIL] Redigir relatório final do projeto
      Responsável: Matheus Virgolino
      Descrição: Consolidar os resultados dos experimentos em um relatório acadêmico,
                 incluindo tabelas e gráficos comparativos (antes vs depois) para cada
                 otimização implementada.

- [ ] [UTIL] Workshop de Git/GitHub para a equipe
      Responsável: Lucas Gabriel
      Descrição: Atividade externa ao repositório. Capacitar os membros da equipe
                 no uso de Git e GitHub, cobrindo o fluxo de trabalho definido em
                 contribution.md (submódulos, branches, PRs).

---

## TINYDB
# Testes existentes: tests/test_tinydb.py, test_operations.py, test_queries.py,
#                    test_storages.py, test_tables.py, test_middlewares.py,
#                    test_utils.py (rodar com: pytest)

### Otimização 1 — B-Trees para substituição da busca sequencial

- [ ] [IMP] TinyDB: Implementar B-Trees no núcleo de armazenamento
      Responsável: Manoel
      Descrição: Substituir o método de busca sequencial por B-Trees, permitindo
                 acesso direto a partes específicas do arquivo em disco e eliminando
                 a necessidade de carregar o JSON inteiro em memória a cada consulta.

- [ ] [VAL] TinyDB: Validar implementação das B-Trees
      Responsável: Lucas
      Descrição: Executar a suíte de testes existente (pytest em tinydb/tests/) e
                 confirmar que todos passam. Revisar legibilidade e mantenabilidade
                 do código implementado.

- [ ] [PERF] TinyDB: Medir performance das B-Trees
      Responsável: Lucas
      Descrição: Executar testes de estresse com mais de 1 milhão de registros.
                 Métrica: tempo de resposta em inserções e buscas.
                 Comparar com o processamento padrão do TinyDB.
                 Mínimo de 30 execuções. Salvar resultado em results/tinydb/.

### Otimização 2 — Filtros de Bloom para consultas negativas

- [ ] [IMP] TinyDB: Implementar Filtros de Bloom
      Responsável: Lucas
      Descrição: Adicionar Filtros de Bloom como camada de teste rápido para
                 descartar leituras desnecessárias em buscas por registros inexistentes,
                 confirmando a ausência antes de acessar o sistema de arquivos.

- [ ] [VAL] TinyDB: Validar implementação dos Filtros de Bloom
      Responsável: Manoel
      Descrição: Executar a suíte de testes existente (pytest em tinydb/tests/) e
                 confirmar que todos passam. Revisar o código implementado e garantir
                 que o comportamento original da biblioteca foi mantido.

- [ ] [PERF] TinyDB: Medir performance dos Filtros de Bloom
      Responsável: Manoel
      Descrição: Monitorar uso de CPU e disco durante milhares de consultas por
                 chaves inexistentes. Métrica: número de leituras em disco barradas
                 e tempo total de execução.
                 Mínimo de 30 execuções. Salvar resultado em results/tinydb/.

---

## PYTHON-DOTENV
# Testes existentes: tests/ (rodar com: pytest)

### Otimização 1 — ChainMap para substituição da interpolação por cópia

- [ ] [IMP] Python-dotenv: Implementar ChainMap na interpolação de variáveis
      Responsável: Railton
      Descrição: Substituir a estratégia atual de cópia e mesclagem física de
                 dicionários pela estrutura ChainMap (collections). Eliminar a
                 complexidade O(N(N+E)) reduzindo o overhead de merge de dicionários
                 em ambientes de configuração densos.

- [ ] [VAL] Python-dotenv: Validar implementação do ChainMap
      Responsável: João
      Descrição: Executar a suíte de testes existente (pytest em python-dotenv/tests/)
                 e confirmar que todos passam. Revisar o código implementado e garantir
                 que o comportamento original da biblioteca foi mantido.

- [ ] [PERF] Python-dotenv: Medir performance do ChainMap
      Responsável: Railton
      Descrição: Benchmark com arquivos .env de larga escala (centenas de variáveis
                 com interpolações aninhadas). Métrica: tempo total de execução de CPU.
                 Comparar implementação baseada em cópias vs ChainMap.
                 Mínimo de 30 execuções. Salvar resultado em results/python-dotenv/.

---

## WHOOSH-RELOADED
# Testes existentes: tests/test_indexing.py, test_searching.py, test_parsing.py,
#                    test_matching.py, test_queries.py, test_writing.py e outros
#                    (rodar com: pytest)

### Otimização 1 — Filtros de Bloom para negative lookups

- [ ] [IMP] Whoosh: Implementar Filtros de Bloom para consultas negativas
      Responsável: Pedro
      Descrição: Integrar Filtros de Bloom para reduzir latência em consultas por
                 termos inexistentes, evitando o custo de leitura em disco ao confirmar
                 a ausência de dados diretamente na memória.

- [ ] [VAL] Whoosh: Validar implementação dos Filtros de Bloom
      Responsável: Virgolino
      Descrição: Executar a suíte de testes existente (pytest em whoosh-reloaded/tests/)
                 e confirmar que todos passam. Revisar o código implementado e garantir
                 que o comportamento original foi mantido.

- [ ] [PERF] Whoosh: Medir performance dos Filtros de Bloom (negative lookup)
      Responsável: Virgolino
      Descrição: Submeter milhares de consultas por termos inexistentes em um índice
                 populado com 500 mil documentos.
                 Métricas: tempo total de execução e número de chamadas de leitura
                 ao sistema de arquivos.
                 Mínimo de 30 execuções. Salvar resultado em results/whoosh-reloaded/.

### Otimização 2 — Skip Lists para consultas booleanas

- [ ] [IMP] Whoosh: Implementar Skip Lists para cruzamento de listas invertidas
      Responsável: Pedro
      Descrição: Adotar Skip Lists para acelerar o cruzamento de informações em
                 consultas booleanas, reduzindo a complexidade da interseção de
                 listas de varredura linear para logarítmica.

- [ ] [VAL] Whoosh: Validar implementação das Skip Lists
      Responsável: Virgolino
      Descrição: Executar a suíte de testes existente (pytest em whoosh-reloaded/tests/)
                 e confirmar que todos passam. Revisar o código implementado e garantir
                 que o comportamento original foi mantido.

- [ ] [PERF] Whoosh: Medir performance das Skip Lists (consultas booleanas)
      Responsável: Virgolino
      Descrição: Benchmark de interseção cruzando termos de altíssima e baixíssima
                 frequência. Métrica: tempo de processamento da interseção comparando
                 o matcher original vs versão otimizada.
                 Mínimo de 30 execuções. Salvar resultado em results/whoosh-reloaded/.

### Otimização 3 — Índice de N-gramas para buscas wildcard

- [ ] [IMP] Whoosh: Implementar índice de N-gramas para buscas wildcard
      Responsável: Virgolino
      Descrição: Transformar buscas de sufixos e prefixos (wildcards) em buscas
                 exatas indexadas via N-gramas, eliminando a varredura linear de
                 todo o vocabulário.

- [ ] [VAL] Whoosh: Validar implementação do índice de N-gramas
      Responsável: Pedro
      Descrição: Executar a suíte de testes existente (pytest em whoosh-reloaded/tests/)
                 e confirmar que todos passam. Revisar o código implementado e garantir
                 que o comportamento original foi mantido.

- [ ] [PERF] Whoosh: Medir performance do índice de N-gramas (wildcard)
      Responsável: Pedro
      Descrição: Comparar tempo de resposta da varredura linear do léxico vs
                 abordagem com N-gramas em buscas com wildcards (*ados, *ritmo*)
                 em vocabulários de termos técnicos.
                 Mínimo de 30 execuções. Salvar resultado em results/whoosh-reloaded/.

---

## ENVIO AO UPSTREAM (fim do projeto)

- [ ] [UTIL] Abrir PR para o repositório oficial do TinyDB
- [ ] [UTIL] Abrir PR para o repositório oficial do Python-dotenv
- [ ] [UTIL] Abrir PR para o repositório oficial do Whoosh-Reloaded
