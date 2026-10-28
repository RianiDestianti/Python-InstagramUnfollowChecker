import glob
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

rootDir = os.path.dirname(os.path.abspath(__file__))
exportDirs = sorted(glob.glob(os.path.join(rootDir, "instagram-*")))

if not exportDirs:
    sys.exit("Folder export Instagram (instagram-*) tidak ditemukan.")

activityDir = os.path.join(exportDirs[-1], "your_instagram_activity")


def loadEntries(*pathParts):
    path = os.path.join(activityDir, *pathParts)

    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, list):
        return data

    return next((value for value in data.values() if isinstance(value, list)), [])


def findValuesByLabel(node, label, results):
    if isinstance(node, dict):
        if node.get("label") == label and node.get("value"):
            results.append(node["value"])

        for value in node.values():
            findValuesByLabel(value, label, results)

    elif isinstance(node, list):
        for value in node:
            findValuesByLabel(value, label, results)


def parseEntry(entry):
    stringMapData = entry.get("string_map_data")

    if stringMapData:
        owner = (stringMapData.get("Media Owner") or {}).get("value", "")
        text = (stringMapData.get("Comment") or {}).get("value", "")
        timestamp = (stringMapData.get("Time") or {}).get("timestamp", 0)
        return timestamp, owner, text

    usernames = []
    captions = []
    findValuesByLabel(entry, "Nama pengguna", usernames)
    findValuesByLabel(entry, "Keterangan", captions)

    timestamp = entry.get("timestamp") or entry.get("creation_timestamp") or 0
    owner = usernames[0] if usernames else ""
    caption = captions[0] if captions else ""
    return timestamp, owner, caption


def toDate(timestamp):
    return datetime.fromtimestamp(timestamp, timezone.utc) if timestamp else None


def printSummary(title, entries, topCount=8):
    if not entries:
        print(f"\n{title}: (kosong)")
        return

    rows = [parseEntry(entry) for entry in entries]
    timestamps = sorted(timestamp for timestamp, _, _ in rows if timestamp)
    ownerCounts = Counter(owner.lower() for _, owner, _ in rows if owner)

    print(f"\n{'=' * 60}")
    print(f"{title}  —  {len(entries)} entri")
    print("=" * 60)

    if timestamps:
        firstDate = toDate(timestamps[0])
        lastDate = toDate(timestamps[-1])
        print(f"Rentang : {firstDate:%d %b %Y} s/d {lastDate:%d %b %Y}")

    if ownerCounts:
        print(f"\nTop {topCount} akun:")

        for owner, count in ownerCounts.most_common(topCount):
            print(f"  {count:>5}x  @{owner}")

    latestRows = sorted((row for row in rows if row[0]), reverse=True)[:3]

    if latestRows:
        print("\nTerbaru:")

        for timestamp, owner, text in latestRows:
            preview = text.replace("\n", " ")[:60]
            print(f"  {toDate(timestamp):%d %b %Y}  @{owner or '-'}  {preview}")


printSummary("LIKED POSTS (post yang kamu like)", loadEntries("likes", "liked_posts.json"))
printSummary("STORIES VIEWED (story yang kamu tonton)", loadEntries("story_interactions", "stories_viewed.json"))
printSummary("POLLS (polling story yang kamu jawab)", loadEntries("story_interactions", "polls.json"))
printSummary("STORY LIKES (story yang kamu like)", loadEntries("story_interactions", "story_likes.json"))
printSummary("QUIZZES", loadEntries("story_interactions", "quizzes.json"))
printSummary("QUESTIONS", loadEntries("story_interactions", "questions.json"))
printSummary("EMOJI SLIDERS", loadEntries("story_interactions", "emoji_sliders.json"))
printSummary("LIKED COMMENTS (komentar yang kamu like)", loadEntries("likes", "liked_comments.json"))
printSummary("KOMENTAR KAMU DI POST", loadEntries("comments", "post_comments_1.json"))
printSummary("KOMENTAR KAMU DI REELS", loadEntries("comments", "reels_comments.json"))
printSummary("SAVED POSTS (post tersimpan)", loadEntries("saved", "saved_posts.json"))
printSummary("REPOSTS", loadEntries("media", "reposts.json"))
printSummary("STORY YANG KAMU POSTING", loadEntries("media", "stories.json"))
printSummary("POST KAMU", loadEntries("media", "posts.json"))
printSummary("POST ARSIP", loadEntries("media", "archived_posts.json"))
