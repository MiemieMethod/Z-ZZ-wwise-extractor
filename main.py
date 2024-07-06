import json
import xmltodict
import subprocess
import shutil

from wfp.FilePackager import *

bank_dict = {}


# redefine because of there is a print statement in the original function
def fnv_hash_64(data: str):
    hash_num = 14695981039346656037
    data = data.lower().encode()
    for i in data:
        hash_num = ((hash_num * 1099511628211) & 0xffffffffffffffff) ^ i
    return hash_num

def addJsonString(json_data, results=[]):
    if isinstance(json_data, dict):
        for key in json_data:
            if key not in results:
                results.append(key)
            if isinstance(json_data[key], dict) or isinstance(json_data[key], list):
                addJsonString(json_data[key], results)
            elif isinstance(json_data[key], str):
                if json_data[key] not in results:
                    results.append(json_data[key])
    elif isinstance(json_data, list):
        for item in json_data:
            if isinstance(item, dict) or isinstance(item, list):
                addJsonString(item, results)
            elif isinstance(item, str):
                if item not in results:
                    results.append(item)

def outputWwnames():
    result = ""

    result += "\n### LANG NAMES\n"
    for key in ["SFX", "Chinese(PRC)", "English(EN)", "Japanese(JP)", "Korean(KR)"]:
        result += f"{key}\n"

    result += "\n### BRUTE FORCE NAMES\n"
    results = []
    for root, dirs, files in os.walk("data"):
        for file in files:
            if file.endswith(".json"):
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    if file.startswith("TextMap"):
                        continue
                    print(f"[Main] Name fetch: Reading {os.path.join(root, file)}")
                    data = json.load(f)
                    addJsonString(data, results)
    result += "\n".join(results)

    with open("output/unpack/wwnames.txt", "w", encoding="utf-8") as f:
        f.write(result)


def elegantWrite(f, file_data):
    f.write(file_data[0][0])
    if len(file_data) > 1:
        print("[Mian] file name hash collides! Keep the first one.")


def unpackWwiseBanks():
    package = Package()

    if not os.path.exists("output/unpack"):
        os.makedirs("output/unpack")
    if not os.path.exists("input"):
        print("[Main] missing `input` folder!")

    package.addfile(open(f'input/Min/Minimum.pck', 'rb'))
    package.addfile(open(f'input/Full/Patch.pck', 'rb'))
    for i in range(0, 15):
        package.addfile(open(f'input/Full/SoundBank_SFX_{i}.pck', 'rb'))
    # for i in range(0, 32):
    #     package.addfile(open(f'input/Music{i}.pck', 'rb'))
    for i in range(0, 15):
        package.addfile(open(f'input/Full/Streamed_SFX_{i}.pck', 'rb'))
    # for i in range(0, 32):
    #     package.addfile(open(f'input/SFX/External{i}.pck', 'rb'))
    for i in ["Cn", "En", "Jp", "Kr"]:
        if os.path.exists(f"input/Full/{i}"):
            package.addfile(open(f'input/Full/{i}/Patch.pck', 'rb'))
            package.addfile(open(f'input/Full/{i}/SoundBank_{i}_0.pck', 'rb'))
            package.addfile(open(f'input/Full/{i}/Streamed_{i}_0.pck', 'rb'))
            for j in range(0, 15):
                package.addfile(open(f'input/Full/{i}/External_{i}_{j}.pck', 'rb'))
            # for j in range(0, 32):
            #     package.addfile(open(f'input/{i}/VoBanks{j}.pck', 'rb'))

    for i in ["SFX", "Chinese(PRC)", "English(EN)", "Japanese(JP)", "Korean(KR)"]:
        if not os.path.exists(f"output/unpack/{i.lower()}"):
            os.makedirs(f"output/unpack/{i.lower()}")
        if i.upper() in package.LANGUAGE_DEF:
            langcode = package.LANGUAGE_DEF[i.upper()]
        else:
            continue
        if len(package.map[0]) > 0 and langcode in package.map[0]:
            for j in package.map[0][langcode]:
                file_data = package.get_file_data_by_hash(j, langcode, 0)
                with open(f'output/unpack/{i.lower()}/{j}.bnk', 'wb') as f:
                    elegantWrite(f, file_data)
        if len(package.map[1]) > 0 and langcode in package.map[1]:
            for j in package.map[1][langcode]:
                file_data = package.get_file_data_by_hash(j, langcode, 1)
                with open(f'output/unpack/{i.lower()}/{j}.wem', 'wb') as f:
                    elegantWrite(f, file_data)
        if len(package.map[2]) > 0 and langcode in package.map[2]:
            for j in package.map[2][langcode]:
                file_data = package.get_file_data_by_hash(j, langcode, 2)
                if not os.path.exists(f"output/unpack/{i.lower()}/externals"):
                    os.makedirs(f"output/unpack/{i.lower()}/externals")
                with open(f'output/unpack/{i.lower()}/externals/{j}.wem', 'wb') as f:
                    elegantWrite(f, file_data)


def generateBankData():
    result = subprocess.run(['python', 'wwiser.pyz', '-d', 'xml', '-dn', './output/unpack/banks', './output/unpack/**/*.bnk'],
                            capture_output=True, text=True)
    print(result.stdout)


def loadBankXml():
    global bank_dict
    with open("output/unpack/banks.xml", 'r') as f:
        xml_string = f.read()
    if os.path.exists("output/unpack/banks_temp.json"):
        with open("output/unpack/banks_temp.json", 'r') as f:
            bank_dict_old = json.load(f)
            # if bank_dict_old["hash"] == fnv_hash_64(xml_string):
            bank_dict = bank_dict_old
            return
    data_dict = xmltodict.parse("<base>" + xml_string + "</base>")
    for bank in data_dict["base"]["root"]:
        bank_cont = parseXmlNode(bank)
        hash_map = {}
        for i in ["SFX", "Chinese(PRC)", "English(EN)", "Japanese(JP)", "Korean(KR)"]:
            hash_map[fnv_hash_32(i)] = i
        lang = bank_cont["BankHeader"]["AkBankHeader"]["dwLanguageID"]["@value"]
        if lang not in bank_dict:
            bank_dict[lang] = {}
        bank_dict[lang][bank["@filename"]] = bank_cont

    with open("output/unpack/banks_temp.json", 'w') as f:
        bank_dict["hash"] = fnv_hash_64(xml_string)
        json.dump(bank_dict, f, indent=4)


def parseXmlNode(node):
    result = node
    parseXmlObj("field", node, result)
    parseXmlObj("object", node, result)
    parseXmlLst(node, result)
    return result


def parseXmlObj(obj_name, obj, result):
    if obj_name in obj:
        if isinstance(obj[obj_name], list):
            for item in obj[obj_name]:
                if item["@name"] not in result:
                    result[item["@name"]] = parseXmlNode(item)
                else:
                    if not isinstance(result[item["@name"]], list):
                        foo = result[item["@name"]]
                        result[item["@name"]] = []
                        result[item["@name"]].append(foo)
                    result[item["@name"]].append(parseXmlNode(item))
        elif isinstance(obj[obj_name], dict):
            result[obj[obj_name]["@name"]] = parseXmlNode(obj[obj_name])
        del result[obj_name]


def parseXmlLst(lst, result):
    if "list" in lst:
        lst = lst["list"]
        if isinstance(lst, list):
            for item in lst:
                result[item["@name"]] = []
                appendXmlLstElement("field", item, result[item["@name"]])
                appendXmlLstElement("object", item, result[item["@name"]])
                appendXmlLstElement("list", item, result[item["@name"]])
        else:
            result[lst["@name"]] = []
            appendXmlLstElement("field", lst, result[lst["@name"]])
            appendXmlLstElement("object", lst, result[lst["@name"]])
            appendXmlLstElement("list", lst, result[lst["@name"]])
        del result["list"]


def appendXmlLstElement(obj_name, obj, lst):
    if obj_name in obj:
        if isinstance(obj[obj_name], list):
            for item in obj[obj_name]:
                lst.append(parseXmlNode(item))
        elif isinstance(obj[obj_name], dict):
            lst.append(parseXmlNode(obj[obj_name]))
        del obj[obj_name]


skip_num = 0
completed_files = []


def elegantRename(hash_path, voice_path, ext="wem", log_area="External"):
    old_file_name = f"output/unpack/{hash_path}.{ext}"
    new_file_name = f"output/rename/{voice_path}.{ext}"
    if os.path.exists(new_file_name):
        os.remove(new_file_name)
    global completed_files
    if os.path.exists(old_file_name):
        shutil.copy2(old_file_name, new_file_name)
        if old_file_name not in completed_files:
            completed_files.append(old_file_name)
    else:
        print(f"[{log_area}] {old_file_name} -> {new_file_name} not found!")
        global skip_num
        skip_num += 1


def deleteCompletedFiles():
    global completed_files
    with open("output/unpack/finished.txt", "w", encoding="utf-8") as f:
        for file in completed_files:
            f.write(file + "\n")
    for file in completed_files:
        os.remove(file)
    completed_files = []


def renameExtrenalWems():
    if not os.path.exists(f"output/rename"):
        os.makedirs(f"output/rename")

    for i in ["Chinese(PRC)", "English(EN)", "Japanese(JP)", "Korean(KR)", "Cn", "En", "Jp", "Kr"]:
        with open("data/Data/AudioResourceData.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            for key in data["externals"]:
                entry = data["externals"][key]
                for j in ["wem", "ogg", "wav", "mp3"]:
                    path = f"{entry["prefix"]}{i}/{key}"
                    hash = fnv_hash_64(f"{path}.{j}")
                    elegantRename(f"sfx/externals/{hash}", path)
                # hash = fnv_hash_64(f"{entry["prefix"]}{key}_{i}.wem")
                # elegantRename(f"sfx/externals/{hash}", f"{i.lower()}/voice/{entry["prefix"]}{key}")

    global skip_num
    print(f"[External] skipped {skip_num} files because of unfound hash.")
    skip_num = 0


def renameEventWems():
    def getLoadedItems(bank):
        hirc = bank.get("HircChunk", {})
        loaded_items = hirc.get("listLoadedItem", [])
        loaded_items_map = {}
        for item in loaded_items:
            loaded_items_map[item.get("ulID", item.get("ulStateID", ""))["@value"]] = item
        return loaded_items_map

    def findAudioNode(nodes, audioNodeIdToName):
        for node in nodes:
            if "audioNodeId" in node:
                if node["key"]["@value"] != "0":
                    audioNodeIdToName[node["audioNodeId"]["@value"]] = node["key"].get("@hashname",
                                                                                       node["key"]["@value"])
            elif "pNodes" in node:
                findAudioNode(node["pNodes"], audioNodeIdToName)

    def getChilds(node, result):
        if "ulNumChilds" in node:
            if int(node["ulNumChilds"]["@value"]) > 0:
                if int(node["ulNumChilds"]["@value"]) == 1:
                    result.append(node["ulChildID"]["@value"])
                else:
                    for child in node["ulChildID"]:
                        result.append(child["@value"])
        return result

    def findMusicSound(sound_id, musicSegments, musicTracks, musicRanSeqCntrs, musicSwitchCntrs, path, result):
        if sound_id in musicSwitchCntrs:
            for child in musicSwitchCntrs[sound_id]:
                subpath = path
                subpath += f"/{musicSwitchCntrs[sound_id][child]}"
                findMusicSound(child, musicSegments, musicTracks, musicRanSeqCntrs, musicSwitchCntrs, subpath, result)
        if sound_id in musicRanSeqCntrs:
            childs = []
            getChilds(musicRanSeqCntrs[sound_id], childs)
            for child in childs:
                findMusicSound(child, musicSegments, musicTracks, musicRanSeqCntrs, musicSwitchCntrs, path, result)
        if sound_id in musicSegments:
            childs = []
            getChilds(musicSegments[sound_id], childs)
            for child in childs:
                findMusicSound(child, musicSegments, musicTracks, musicRanSeqCntrs, musicSwitchCntrs, path, result)
        if sound_id in musicTracks:
            for source in musicTracks[sound_id]:
                subpath = path
                subpath += f"/{source["AkMediaInformation"]["sourceID"]["@value"]}"
                result[source["AkMediaInformation"]["sourceID"]["@value"]] = subpath

    if not os.path.exists(f"output/rename"):
        os.makedirs(f"output/rename")

    for lang in bank_dict:
        if lang == "hash":
            continue
        for bank_name in bank_dict[lang]:
            # print(f"[Event] {bank_name}")
            bank = bank_dict[lang][bank_name]

            loaded_items_map = getLoadedItems(bank)

            processed = False
            global completed_files

            for item_id in loaded_items_map:
                item = loaded_items_map[item_id]
                if item["@name"] == "CAkEvent":
                    event_id = item["ulID"]["@value"]
                    event_name = item["ulID"].get("@hashname", event_id)
                    for action in item["EventInitialValues"]["actions"]:
                        action_item = loaded_items_map[action["ulActionID"]["@value"]]
                        if action_item["@name"] == "CAkActionPlay":
                            params = action_item["ActionInitialValues"]["PlayActionParams"]
                            for sound_lang in bank_dict:
                                if params["bankID"]["@value"] + ".bnk" in bank_dict[sound_lang]:
                                    sound_bank = bank_dict[params["bankID"]["@value"] + ".bnk"]
                                    sound_bank_loaded_items_map = getLoadedItems(sound_bank)

                                    musicSwitchCntrs = {}
                                    musicRanSeqCntrs = {}
                                    musicSegments = {}
                                    musicTracks = {}

                                    sound_processed = False

                                    normal_sound_path = sound_bank["@path"].replace("\\", "/").replace("./", "")
                                    for sound_id in sound_bank_loaded_items_map:
                                        sound_item = sound_bank_loaded_items_map[sound_id]
                                        if sound_item["@name"] == "CAkSound":
                                            source = sound_item["SoundInitialValues"]["AkBankSourceData"]
                                            type = source["StreamType"]["@value"]
                                            if type == "0":
                                                name = sound_bank["@filename"][:-4]
                                                file_ext = "bnk"
                                                file_index = ""
                                            else:
                                                name = source["AkMediaInformation"]["sourceID"]["@value"]
                                                file_ext = "wem"
                                                file_index = f"{sound_item["@index"]}~"
                                            file2rename = f"{normal_sound_path[14:]}/{name}"
                                            file_destination = f"{normal_sound_path[14:]}/{event_name}/{file_index}{name}"
                                            if not os.path.exists(
                                                    f"output/rename/{normal_sound_path[14:]}/{event_name}"):
                                                os.makedirs(f"output/rename/{normal_sound_path[14:]}/{event_name}")
                                            elegantRename(file2rename, file_destination, file_ext, "Event")
                                            sound_processed = True

                                        if sound_item["@name"] == "CAkMusicSwitchCntr":
                                            node_id2name = {}
                                            findAudioNode(
                                                sound_item["MusicSwitchCntrInitialValues"]["AkDecisionTree"]["pNodes"],
                                                node_id2name)
                                            musicSwitchCntrs[sound_item["ulID"]["@value"]] = node_id2name
                                            sound_processed = True
                                        if sound_item["@name"] == "CAkMusicRanSeqCntr":
                                            musicRanSeqCntrs[sound_item["ulID"]["@value"]] = \
                                                sound_item["MusicRanSeqCntrInitialValues"]["MusicTransNodeParams"][
                                                    "MusicNodeParams"][
                                                    "Children"]
                                        if sound_item["@name"] == "CAkMusicSegment":
                                            musicSegments[sound_item["ulID"]["@value"]] = \
                                                sound_item["MusicSegmentInitialValues"]["MusicNodeParams"]["Children"]
                                        if sound_item["@name"] == "CAkMusicTrack":
                                            musicTracks[sound_item["ulID"]["@value"]] = \
                                            sound_item["MusicTrackInitialValues"][
                                                "pSource"]

                                    if action_item["ActionInitialValues"]["idExt"][
                                        "@value"] in sound_bank_loaded_items_map:
                                        initial_item = sound_bank_loaded_items_map[
                                            action_item["ActionInitialValues"]["idExt"]["@value"]]
                                        if initial_item["@name"] == "CAkMusicSwitchCntr":
                                            path = f"{normal_sound_path[14:]}/{event_name}"
                                            filehash2filepath = {}
                                            findMusicSound(initial_item["ulID"]["@value"], musicSegments, musicTracks,
                                                           musicRanSeqCntrs, musicSwitchCntrs, path, filehash2filepath)
                                            for filehash in filehash2filepath:
                                                file2rename = f"{normal_sound_path[14:]}/{filehash}"
                                                file_destination = filehash2filepath[filehash]
                                                if not os.path.exists(
                                                        "output/rename/" + file_destination.replace(f"/{filehash}",
                                                                                                    "")):
                                                    os.makedirs(
                                                        "output/rename/" + file_destination.replace(f"/{filehash}", ""))
                                                elegantRename(file2rename, file_destination, "wem", "Event")

                                    if sound_processed and f"{normal_sound_path}/{sound_bank["@filename"]}" not in completed_files:
                                        completed_files.append(f"{normal_sound_path}/{sound_bank["@filename"]}")

                    processed = True

            normal_path = bank["@path"].replace("\\", "/").replace("./", "")
            if processed and f"{normal_path}/{bank["@filename"]}" not in completed_files:
                completed_files.append(f"{normal_path}/{bank["@filename"]}")

    global skip_num
    print(f"[Event] skipped {skip_num} files because of unfound hash.")
    skip_num = 0

if __name__ == '__main__':
    print("[Main] Start!")
    print("[Main] Start unpacking Wwise banks...")
    # unpackWwiseBanks()
    print("[Main] Start outputting wwnames...")
    # outputWwnames()
    # if you just want to unpack but not rename, comment all lines below
    print("[Main] Start generating bank data...")
    # generateBankData()
    print("[Main] Start loading bank xml...")
    loadBankXml()
    print("[Main] Start renaming external wems...")
    # renameExtrenalWems()
    print("[Main] Start renaming event wems...")
    renameEventWems()
    print("[Main] Start deleting completed files...")
    # this program will delete the files in the `output/unpack` folder which are successfully renamed.
    # if you want to keep them, comment the line below.
    # deleteCompletedFiles()
    print("[Main] Done!")
