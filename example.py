from config_manager.config_manager import ConfigManager

if __name__ == "__main__":
    # Загрузка конфига из файла
    cfg_path = "vlmhyperbench/cfg/VLMHyperBench_config.json"

    # Создаем конфиг для VLMHyperBench по умолчанию
    config = ConfigManager(cfg_path, default=True)
    print(config.cfg)

    # Пример сохранения
    config.write_config()

    # Получим маппинг директорий для Docker-контейнера
    for host_path, container_path in config.volumes.items():
        print(host_path, container_path)

    # Получим конфиг директорий для Docker-контейнера
    print(config.cfg_container)

    # Получим список python-пакетов для каждого этапа работы
    vlm_run_packages = config.load_packages("vlm_run")
    eval_run_packages = config.load_packages("eval_run")
    
    print("vlm_run_packages:")
    for package in vlm_run_packages:
        print(package)
        
    print("eval_run_packages:")
    for package in eval_run_packages:
        print(package)
