import glob
import json
import os
import sys
from datetime import datetime, timezone

rootDir = os.path.dirname(os.path.abspath(__file__))
exportDirs = sorted(glob.glob(os.path.join(rootDir, "instagram-*")))

if not exportDirs:
    sys.exit("Folder export Instagram (instagram-*) tidak ditemukan.")

exportDir = exportDirs[-1]
connectionsDir = os.path.join(exportDir, "connections", "followers_and_following")
activityDir = os.path.join(exportDir, "your_instagram_activity")

activitySources = [
    ("story_interactions", "stories_viewed.json"),
    ("story_interactions", "story_likes.json"),
    ("story_interactions", "polls.json"),
    ("story_interactions", "quizzes.json"),
    ("story_interactions", "emoji_sliders.json"),
    ("story_interactions", "questions.json"),
    ("likes", "liked_posts.json"),
    ("likes", "liked_comments.json"),
    ("comments", "post_comments_1.json"),
    ("comments", "reels_comments.json"),
]


def extractUsernames(entries):
    usernames = set()

    for item in entries:
        for account in item.get("string_list_data", []):
            username = account.get("value") or item.get("title")

            if username:
                usernames.add(username.lower())

    return usernames


def loadFollowing():
    path = os.path.join(connectionsDir, "following.json")

    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return extractUsernames(data["relationships_following"])


def findUsernames(node, results):
    if isinstance(node, dict):
        if node.get("label") == "Nama pengguna" and node.get("value"):
            results.add(node["value"].lower())

        for value in node.values():
            findUsernames(value, results)

    elif isinstance(node, list):
        for value in node:
            findUsernames(value, results)


def collectLastInteractions():
    lastInteractions = {}

    for folder, fileName in activitySources:
        path = os.path.join(activityDir, folder, fileName)

        if not os.path.exists(path):
            continue

        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, list):
            entries = data
        else:
            entries = next((value for value in data.values() if isinstance(value, list)), [])

        for entry in entries:
            if not isinstance(entry, dict):
                continue

            timestamp = entry.get("timestamp")
            usernames = set()
            findUsernames(entry, usernames)

            if not timestamp or not usernames:
                continue

            for username in usernames:
                if timestamp > lastInteractions.get(username, 0):
                    lastInteractions[username] = timestamp

    return lastInteractions


def daysAgo(timestamp, referenceDate):
    return (referenceDate - datetime.fromtimestamp(timestamp, timezone.utc)).days


following = loadFollowing()
lastInteractions = collectLastInteractions()

allTimestamps = list(lastInteractions.values())
latestDate = datetime.fromtimestamp(max(allTimestamps), timezone.utc)
earliestDate = datetime.fromtimestamp(min(allTimestamps), timezone.utc)

thresholdDays = int(sys.argv[1]) if len(sys.argv) > 1 else 90

neverInteracted = sorted(username for username in following if username not in lastInteractions)
interactedAccounts = sorted(
    (
        (daysAgo(lastInteractions[username], latestDate), username)
        for username in following
        if username in lastInteractions
    ),
    reverse=True,
)
inactiveAccounts = [
    (days, username)
    for days, username in interactedAccounts
    if days >= thresholdDays
]

print("=" * 56)
print(f"PERKIRAAN AKUN JARANG AKTIF - @{os.path.basename(exportDir).split('-')[1]}")
print("=" * 56)
print(f"\nRentang data export : {earliestDate:%d %b %Y} s/d {latestDate:%d %b %Y}")
print(f"Total following     : {len(following)}")
print(f"Ada jejak interaksi : {len(following) - len(neverInteracted)}")
print(f"Tanpa jejak apa pun : {len(neverInteracted)}")
print(f"Interaksi >= {thresholdDays} hari : {len(inactiveAccounts)}")

print(f"\n--- TIDAK PERNAH muncul di aktivitasmu ({len(neverInteracted)}) ---\n")

for username in neverInteracted:
    print(f"@{username}")

print(f"\n--- TERAKHIR interaksi >= {thresholdDays} hari lalu ({len(inactiveAccounts)}) ---\n")

for days, username in inactiveAccounts:
    interactionDate = datetime.fromtimestamp(lastInteractions[username], timezone.utc)
    print(f"{days:>4} hari lalu  ({interactionDate:%d %b %Y})  @{username}")

outputFileName = "inactiveAccounts.txt"
outputPath = os.path.join(rootDir, outputFileName)

with open(outputPath, "w", encoding="utf-8") as file:
    file.write(f"TIDAK PERNAH muncul ({len(neverInteracted)}):\n")

    for username in neverInteracted:
        file.write(f"@{username}\n")

    file.write(f"\nTERAKHIR >= {thresholdDays} hari lalu ({len(inactiveAccounts)}):\n")

    for days, username in inactiveAccounts:
        file.write(f"{days} hari - @{username}\n")

print(f"\nHasil disimpan ke: {outputFileName}")
