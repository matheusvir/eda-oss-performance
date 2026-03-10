import os

_ENV_VARS = ["HOME", "PATH", "USER"]


def generate_dotenv(num_vars: int) -> None:
    output_path = f"./without_interpolation/{num_vars}_simple_variables.env"
    lines = [f"VAR_{i}=value_{i}" for i in range(num_vars)]
    with open(output_path, "w") as f:
        f.write("\n".join(lines) + "\n")


def generate_dotenv_interpolated(num_vars: int) -> None:
    output_path = f"./with_interpolation/{num_vars}_interpolated_variables.env"
    os.makedirs("./with_interpolation", exist_ok=True)
    env_count = len(_ENV_VARS)
    lines = []
    for i in range(num_vars):
        env_var = _ENV_VARS[i % env_count]
        kind = i % 3
        if kind == 0 or i == 0:
            line = f"VAR_{i}=${{{env_var}}}_{i}"
        elif kind == 1:
            line = f"VAR_{i}=${{VAR_{i - 1}}}_{i}"
        else:
            prior = i - (i % 3)
            line = f"VAR_{i}=${{VAR_{prior}}}_{{{env_var}}}_{i}"
        lines.append(line)
    with open(output_path, "w") as f:
        f.write("\n".join(lines) + "\n")


RUNS = 30
START = 10
END = 25_000
RATIO = (END / START) ** (1 / (RUNS - 1))

sizes = [round(START * RATIO**i) for i in range(RUNS - 1)] + [END]

for size in sizes:
    generate_dotenv(size)
    generate_dotenv_interpolated(size)

