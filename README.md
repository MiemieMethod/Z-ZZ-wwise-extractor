# WWISE Extractor

An extractor of wwise audios (with auto rename) for a certain action anime game.

## Use

Just run `main.py` and it will extract all the audios in the `pck` files in the `output/unpack` folder and rename them into the `output/rename` folder.

Notice: please create an `input` folder at the root and put the `pck` files in it. The `pck` should be structured as in game assets. eg. `input/Min/Mimimum.pck`.

Voice-overs are unavailable because of not knowing exact external names. SFXs will be renamed as `<real_event_name>/<original_hash_name>.wem/bnk`. BGMs will be renamed as `<real_event_name>/<audio/switch/node/names>/<original_hash_name>.wem`.

Because of the limitation of the wwise file structure, many of the original names of the audio files are under no hint, and then the extractor will not be able to extract the original name of the audio file but only the event name shown in ExcelConfigs. Moreover, the known event names are also not enough to cover all the audio files, so if you get any hint of the original name / event name of the audio files, please contribute to this repo, [`wwiser-utils`](https://github.com/bnnm/wwiser-utils) repo (under `wwnames` folder) or let me know.