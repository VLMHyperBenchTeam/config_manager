import json
import os
from typing import Any, Dict, List


class ConfigManager:
    def __init__(self, cfg_path: str, default: bool = False) -> None:
        """Инициализирует ConfigManager управляющий конфигурацией VLMHyperbecnh.

        Args:
            cfg_path (str): Путь к файлу конфигурации
            default (bool, optional): Флаг для инициализации конфига по умолчанию.
                По умолчанию False.

        Raises:
            FileNotFoundError: Если файл не найден при default=False
        """
        self.cfg_path = cfg_path

        if default:
            self.cfg = self.get_default_config()
        else:
            self.cfg = self.read_config(cfg_path)

        self.volumes = self.get_volumes()
        self.cfg_container = self.get_container_config()

    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """Возвращает конфигурацию по умолчанию для VLMHyperbench.
        Стандартная конфигурация содержит предустановленные пути к директориям
        данных и системным файлам, как это рекомендуется для типовой установки.
        Returns:
            Dict[str, Any]: Словарь конфигурации с вложенными структурами:
                - data_dirs (Dict[str, str]): Пути к данным
                - system_dirs (Dict[str, str]): Системные директории
        Example:
            >>> default_cfg = ConfigManager.get_default_config()
            >>> print(default_cfg['data_dirs']['vlm_base'])
            'vlmhyperbench/vlm_base.csv'
        """
        default_cfg = {
            "user_config": "user_config_prompt_eval.csv",
            "vlm_base": "vlmhyperbench/vlm_base.csv",
            "data_dirs": {
                "datasets": "vlmhyperbench/data_dirs/Datasets",
                "model_answers": "vlmhyperbench/data_dirs/ModelsAnswers",
                "model_metrics": "vlmhyperbench/data_dirs/ModelsMetrics",
                "prompt_collections": "vlmhyperbench/data_dirs/PromptCollections",
                "system_prompts": "vlmhyperbench/data_dirs/SystemPrompts",
                "reports": "vlmhyperbench/data_dirs/Reports",
            },
            "system_dirs": {
                "cfg": "vlmhyperbench/system_dirs/cfg",
                "bench_stages": "vlmhyperbench/system_dirs/bench_stages",
                "model_cache": "vlmhyperbench/system_dirs/model_cache",
                "wheels": "vlmhyperbench/system_dirs/wheels",
            },
            "eval_docker_img": "ghcr.io/vlmhyperbenchteam/metric-evaluator:python3.10-slim_v0.1.0",
        }

        default_cfg["benchmark_run_cfg"] = os.path.join(
            default_cfg["system_dirs"]["cfg"], "BenchmarkRunConfig.json"
        )
        default_cfg["vlm_run_packages"] = os.path.join(
            default_cfg["system_dirs"]["cfg"], "vlm_run_requirements.txt"
        )
        default_cfg["eval_run_packages"] = os.path.join(
            default_cfg["system_dirs"]["cfg"], "eval_run_requirements.txt"
        )

        return default_cfg

    def write_config(self) -> None:
        """Сохраняет конфигурацию в JSON файл.

        Сохраняет текущее состояние cfg в файл с отступами и поддержкой Unicode.
        Использует путь, указанный в self.cfg_path.

        Raises:
            IOError: При ошибках записи файла
        """
        with open(self.cfg_path, "w", encoding="utf-8") as f:
            json.dump(self.cfg, f, ensure_ascii=False, indent=4)

    @staticmethod
    def read_config(cfg_path: str) -> Dict[str, Any]:
        """Читает конфигурацию из JSON файла

        Args:
            cfg_path (str): Путь к файлу конфигурации

        Returns:
            Dict[str, Any]: Словарь с конфигурационными данными

        Raises:
            FileNotFoundError: Если файл не существует
            JSONDecodeError: При некорректном формате JSON
        """
        with open(cfg_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_volumes(self, base_container_path: str = "workspace") -> Dict[str, str]:
        """Формирует маппинг директорий для Docker-контейнера.

        Создает словарь с путями на хосте и соответствующими путями внутри контейнера.
        Параметр base_container_path позволяет задать базовый путь внутри контейнера,
        как это часто требуется в конфигурациях CI/CD.

        Args:
            base_container_path (str): Базовый путь внутри контейнера.
                По умолчанию "workspace".

        Returns:
            Dict[str, str]: Словарь, осуществляющий маппинг директорий, которые будут примонтированы
            к запущенному Docker-контейнеру.
            Ключи — пути на хосте, значения — пути внутри контейнера.

        Raises:
            OSError: При ошибках обработки путей
        """
        volumes = {}
        for dir_type in ["data_dirs", "system_dirs"]:
            for dir_name, host_path in self.cfg.get(dir_type, {}).items():
                container_path = os.path.join(
                    "/", base_container_path, dir_type, dir_name
                )
                volumes[host_path] = container_path
        return volumes

    def get_container_config(self) -> Dict[str, Any]:
        """Возвращает конфигурацию с путями внутри Docker-контейнера.
        Формирует словарь аналогичной структуры с self.cfg, но значениями
        являются пути внутри контейнера из self.volumes.
        Returns:
            Dict[str, Any]: Конфигурация с путями контейнера
        """
        container_cfg = {}
        for dir_type in ["data_dirs", "system_dirs"]:
            if dir_type in self.cfg:
                container_cfg[dir_type] = {}
                # Итерируемся только по ключам (dir_name), так как host_path не нужен
                for dir_name in self.cfg[dir_type]:
                    container_dir = os.path.join("/", "workspace", dir_type, dir_name)
                    container_cfg[dir_type][dir_name] = container_dir
        return container_cfg

    def load_packages(self, package_type: str) -> List[str]:
        """
        Загружает список пакетов из файла с требованиями

        Args:
            package_type (str): Тип пакетов ('vlm_run' или 'eval_run')

        Returns:
            List[str]: Список URL пакетов

        Raises:
            ValueError: При некорректном типе пакетов
            FileNotFoundError: Если файл требований не найден
        """
        if package_type not in ("vlm_run", "eval_run"):
            raise ValueError("package_type должен быть 'vlm_run' или 'eval_run'")

        file_key = f"{package_type}_packages"
        file_path = self.cfg.get(file_key)

        if not file_path or not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл {file_path} не найден")

        with open(file_path, "r") as f:
            packages = [line.strip() for line in f if line.strip()]

        return packages
