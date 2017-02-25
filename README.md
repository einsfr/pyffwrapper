# pyffwrapper

Python-обёртка для работы с бинарными файлами [FFmpeg](https://ffmpeg.org). Предназначена для использования в проектах, работающих с FFmpeg.

## Использование

* Создаём экземпляр фабрики команд для ffmpeg `factory.FFmpegFactory` и экземпляр фабрики команд для ffprobe `factory.FFprobeFactory`, сохраняем их в соответствующих переменных этого модуля. Не обязательно создавать их все - достаточно будет только тех, что предполагается использовать.
* Создаём экземпляр загрузчика профилей `profile_loader.ProfileLoader` и сохраняем его в переменной модуля `profile_loader`. Это не обязательно, если профили использоваться не будут.
* С помощью фабрик создаём экземпляры классов-комманд.
* Запускаем комманду на исполнение с помощью метода `exec`.
