import os
import logging
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler
from moviepy.editor import VideoFileClip

TOKEN = os.environ.get("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a lecture video and I'll cut the first 20 seconds for you!")

async def process_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = update.message.video or update.message.document

    if not video:
        await update.message.reply_text("Please send a video file!")
        return

    file = await context.bot.get_file(video.file_id)
    file_path = f"input_{video.file_id}.mp4"
    output_path = f"output_{video.file_id}.mp4"
    await file.download_to_drive(file_path)

    try:
        clip = VideoFileClip(file_path)
        # Cut from 20 seconds to the end
        if clip.duration > 20:
            new_clip = clip.subclip(20, clip.duration)
        else:
            await update.message.reply_text("Video is shorter than 20 seconds!")
            os.remove(file_path)
            return

        new_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", threads=2, logger=None)
        await update.message.reply_video(video=InputFile(output_path), caption="Here is your video without the first 20 seconds!")

        new_clip.close()
        clip.close()
        os.remove(file_path)
        os.remove(output_path)
    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("Failed to process the video. Please try again.")
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(output_path):
            os.remove(output_path)

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, process_video))
    port = int(os.environ.get("PORT", 8080))
    app.run_polling(stop_signals=None)

if __name__ == "__main__":
    main()
