import os
import subprocess
import argparse
import time
from multiprocessing import Pool


def run_behave(test_directory, behave_args):
    behave_command = f"behave {test_directory} --no-capture --no-skipped --format plain {behave_args}"
    result = subprocess.run(behave_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(2)
    return result


def find_feature_files(directory):
    feature_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.feature'):
                feature_files.append(os.path.join(root, file))
    return feature_files


def generate_test_segments(features_directory, num_processes:int):
    if not os.path.exists(features_directory):
        raise FileNotFoundError(f"Directory '{features_directory}' not found.")
    feature_files = find_feature_files(features_directory)
    print(len(feature_files))
    test_segments = []

    # Calcular el tamaño de los segmentos de manera más precisa
    segment_size, remainder = divmod(len(feature_files), num_processes)

    # Dividir las pruebas en segmentos equitativos
    start_idx = 0
    for i in range(num_processes):
        # Asegurarse de que el último segmento incluya el resto de archivos
        end_idx = start_idx + segment_size + (1 if i < remainder else 0)
        print(f"Start Index {start_idx}")
        print(f"End Index {end_idx}")

        segment = " ".join(feature_files[start_idx:end_idx])  # Unir rutas en una cadena separada por espacios
        print(segment)
        test_segments.append(segment)

        start_idx = end_idx

    return test_segments


def create_feature_path(project, feature):
    return f"features/{project}/{feature}"


def parse_command_line_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-env", "--environment", help="Environment (Eg: develop, qa)", required=True)
    parser.add_argument("-tr", "--testrailReport", help="Testrail Report", required=True)
    parser.add_argument("-dc", "--driverController", help="Driver Controller", required=True)
    parser.add_argument("-sv", "--sentryVersion", help="Sentry Version", required=True)
    parser.add_argument("-act", "--acceptanceTest", help="Acceptance Test (Eg: Regression, Acceptance, Stability)",
                        required=True)
    parser.add_argument("-pro", "--ProjectType", choices=["datahub", "translator", "data_analysis"], required=True)
    parser.add_argument("-ft", "--Feature", help="Feature name", required=True)
    parser.add_argument("-tp", "--proces", help="Total of parallel process", required=True)

    args = parser.parse_args()
    behave_args = (
        f"-Dtest={args.environment} "
        f"-Dtestrail={args.testrailReport} "
        f"-Ddriver={args.driverController} "
        f"-Dapp_version={args.sentryVersion} "
        f"-Dacceptance_tests={args.acceptanceTest} "
        f"-Dproject={args.ProjectType}"
    )
    parallel_options = {
        "project": args.ProjectType,
        "feature_name": args.Feature,
        "total_process": args.proces
    }
    return [behave_args, parallel_options]


if __name__ == "__main__":
    command_line = parse_command_line_args()
    features_directory = create_feature_path(project=command_line[1].get("project"), feature=command_line[1].get("feature_name"))
    num_processes = command_line[1].get("total_process")  # Especifica el número de procesos en paralelo que deseas ejecutar

    test_segments = generate_test_segments(features_directory, int(num_processes))
    print(test_segments)

    with Pool(processes=int(num_processes)) as pool:
        results = pool.starmap(run_behave, [(segment, command_line[0]) for segment in test_segments])

    # Imprime los resultados de las pruebas
    for idx, result in enumerate(results):
        print(f"Resultado de la prueba {idx + 1}:")
        print(result.stdout.decode())
        print(result.stderr.decode())