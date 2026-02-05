from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import asyncio
import os

from parser import TelegramChannelParser

app = FastAPI()

app.mount("/files", StaticFiles(directory="parsed_data"), name="files")

class ParseRequest(BaseModel):
    link: str

parser = TelegramChannelParser(
    api_id=os.getenv("TELEGRAM_API_ID"),
    api_hash=os.getenv("TELEGRAM_API_HASH"),
    phone_number=os.getenv("TELEGRAM_PHONE")
)

@app.post("/parse")
async def parse(req: ParseRequest):
    await parser.connect()

    info = await parser.get_channel_info(req.link)
    participants = await parser.collect_all_participants_comprehensive(req.link)

    os.makedirs("parsed_data", exist_ok=True)
    prefix = f"parsed_data/{info['raw_username'] or 'channel'}"

    csv_file, txt_file = await parser.save_participants_with_progress(
        participants, prefix
    )

    await parser.close()

    return {
        "ok": True,
        "csv": f"files/{os.path.basename(csv_file)}",
        "txt": f"files/{os.path.basename(txt_file)}"
    }
