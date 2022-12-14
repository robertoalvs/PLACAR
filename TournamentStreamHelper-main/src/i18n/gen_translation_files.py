import os

file_list = []

for root, dirs, files in os.walk("src"):
    path = root.split(os.sep)
    print((len(path) - 1) * '---', os.path.basename(root))
    for file in files:
        if file.endswith((".py", ".ui")):
            print(len(path) * '---', file)
            file_list.append(f"{root}/{file}")

print(file_list)

languages = [
    "pt-BR",
    "fr",
    "ja",
    "es",
    "de"
]

output = [f'src/i18n/TSH_{lang}.ts' for lang in languages]

os.system(
    f"lupdate {' '.join(file_list)} -ts {' '.join(output)}")
