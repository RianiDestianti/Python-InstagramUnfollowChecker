import glob
import json
import os
import sys

rootDir = os.path.dirname(os.path.abspath(__file__))
exportDirs = sorted(glob.glob(os.path.join(rootDir, "instagram-*")))

if not exportDirs:
    sys.exit("Folder export Instagram (instagram-*) tidak ditemukan.")

exportDir = exportDirs[-1]
connectionsDir = os.path.join(exportDir, "connections", "followers_and_following")
followersFile = os.path.join(connectionsDir, "followers_1.json")
followingFile = os.path.join(connectionsDir, "following.json")


def extractUsernames(entries):
    usernames = set()

    for item in entries:
        for account in item.get("string_list_data", []):
            username = account.get("value") or item.get("title")

            if not username:
                href = account.get("href", "")
                username = href.rstrip("/").split("/")[-1]

            if username:
                usernames.add(username.lower())

    return usernames


def loadUsernames(path, key=None):
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return extractUsernames(data[key] if key else data)


followers = loadUsernames(followersFile)
following = loadUsernames(followingFile, "relationships_following")

notFollowingBack = following - followers
notFollowedBack = followers - following

print("=" * 50)
print("INSTAGRAM FOLLOW CHECKER")
print(f"@{os.path.basename(exportDir).split('-')[1]}")
print("=" * 50)

print(f"\nTotal followers    : {len(followers)}")
print(f"Total following    : {len(following)}")
print(f"Saling follow      : {len(followers & following)}")
print(f"Tidak follow balik : {len(notFollowingBack)}")
print(f"Belum kamu follbek : {len(notFollowedBack)}")

if "--not-followed-back" in sys.argv:
    title = "Akun yang follow kamu tapi BELUM kamu follow balik:"
    results = notFollowedBack
    outputFileName = "notFollowedBack.txt"
else:
    title = "Akun yang kamu follow tapi TIDAK follow kamu:"
    results = notFollowingBack
    outputFileName = "notFollowingBack.txt"

print(f"\n{title}\n")

for username in sorted(results):
    print(f"@{username}")

outputPath = os.path.join(rootDir, outputFileName)

with open(outputPath, "w", encoding="utf-8") as file:
    for username in sorted(results):
        file.write(f"@{username}\n")

print(f"\nHasil disimpan ke: {outputFileName}")
