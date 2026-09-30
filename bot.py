import os
import asyncio

from dotenv import load_dotenv

from telegram import (
    Update,
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

from scanner import scan_document

from file_tools import (
    convert_image,
    image_to_pdf,
    pdf_to_images,
    audio_to_mp3,
    video_to_mp4,
    is_supported_media_url,
    download_media_link
)


load_dotenv()


BOT_TOKEN = os.getenv(
    "BOT_TOKEN"
)


BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

INCOMING_DIR = os.path.join(
    BASE_DIR,
    "incoming"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "outputs"
)


os.makedirs(
    INCOMING_DIR,
    exist_ok=True
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


MAX_DOWNLOAD_SIZE = (
    20 * 1024 * 1024
)

MAX_UPLOAD_SIZE = (
    50 * 1024 * 1024
)


if not BOT_TOKEN:

    raise RuntimeError(
        "BOT_TOKEN is missing from .env"
    )


def reset_mode(
    context
):

    context.user_data.pop(
        "mode",
        None
    )

    context.user_data.pop(
        "target_format",
        None
    )


def main_menu_keyboard():

    return InlineKeyboardMarkup([

        [

            InlineKeyboardButton(
                "📄 Scan Document",
                callback_data="mode_scan"
            )

        ],

        [

            InlineKeyboardButton(
                "🖼 Convert Image",
                callback_data="choose_image_format"
            )

        ],

        [

            InlineKeyboardButton(
                "📑 Image → PDF",
                callback_data="mode_to_pdf"
            ),

            InlineKeyboardButton(
                "📄 PDF → Images",
                callback_data="mode_pdf_to_image"
            )

        ],

        [

            InlineKeyboardButton(
                "🎵 Audio → MP3",
                callback_data="mode_to_mp3"
            ),

            InlineKeyboardButton(
                "🎬 Video → MP4",
                callback_data="mode_to_mp4"
            )

        ],

        [

            InlineKeyboardButton(
                "❌ Cancel",
                callback_data="cancel_mode"
            )

        ]

    ])


def image_format_keyboard():

    return InlineKeyboardMarkup([

        [

            InlineKeyboardButton(
                "PNG",
                callback_data="format_png"
            ),

            InlineKeyboardButton(
                "JPG",
                callback_data="format_jpg"
            ),

            InlineKeyboardButton(
                "WEBP",
                callback_data="format_webp"
            )

        ],

        [

            InlineKeyboardButton(
                "⬅️ Back",
                callback_data="menu_main"
            )

        ]

    ])


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    reset_mode(
        context
    )


    await update.message.reply_text(

        "🤖 Raspberry Pi File Utility Bot\n\n"
        "Choose a tool below:",

        reply_markup=main_menu_keyboard()

    )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "📖 How to use the bot\n\n"

        "Choose a tool from /start, "
        "then send the requested file or link.\n\n"

        "Documents:\n"
        "/scan\n"
        "/to_pdf\n"
        "/pdf_to_image\n\n"

        "Images:\n"
        "/convert_image\n\n"

        "Media:\n"
        "/to_mp3\n"
        "/to_mp4\n\n"

        "For media links, send a public "
        "YouTube or TikTok URL after choosing "
        "Audio → MP3 or Video → MP4.\n\n"

        "/cancel - Cancel current task"
    )


async def cancel_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    reset_mode(
        context
    )


    await update.message.reply_text(

        "❌ Current task cancelled.",

        reply_markup=main_menu_keyboard()

    )


async def scan_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    reset_mode(
        context
    )


    context.user_data[
        "mode"
    ] = "scan"


    await update.message.reply_text(

        "📄 Document scanner ready.\n\n"

        "Take a clear photo of your document "
        "and send it here.\n\n"

        "For the best quality, send the image "
        "as a file/document."
    )


async def convert_image_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    reset_mode(
        context
    )


    await update.message.reply_text(

        "🖼 Choose an output image format:",

        reply_markup=image_format_keyboard()

    )


async def to_pdf_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    reset_mode(
        context
    )


    context.user_data[
        "mode"
    ] = "to_pdf"


    await update.message.reply_text(

        "📑 Image to PDF ready.\n\n"
        "Send an image."
    )


async def pdf_to_image_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    reset_mode(
        context
    )


    context.user_data[
        "mode"
    ] = "pdf_to_image"


    await update.message.reply_text(

        "📄 PDF to image ready.\n\n"

        "Send a PDF.\n\n"

        "Each page will be returned as "
        "a separate PNG file."
    )


async def to_mp3_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    reset_mode(
        context
    )


    context.user_data[
        "mode"
    ] = "to_mp3"


    await update.message.reply_text(

        "🎵 Audio → MP3 ready.\n\n"

        "Send either an audio file, "
        "a public YouTube link, or "
        "a public TikTok link."
    )


async def to_mp4_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    reset_mode(
        context
    )


    context.user_data[
        "mode"
    ] = "to_mp4"


    await update.message.reply_text(

        "🎬 Video → MP4 ready.\n\n"

        "Send either a video file, "
        "a public YouTube link, or "
        "a public TikTok link."
    )


async def button_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query


    await query.answer()


    data = query.data


    if data == "menu_main":

        reset_mode(
            context
        )


        await query.edit_message_text(

            "🤖 Choose a tool below:",

            reply_markup=main_menu_keyboard()

        )


        return


    if data == "choose_image_format":

        reset_mode(
            context
        )


        await query.edit_message_text(

            "🖼 Choose an output image format:",

            reply_markup=image_format_keyboard()

        )


        return


    if data in (

        "format_png",

        "format_jpg",

        "format_webp"

    ):

        target_format = data.replace(
            "format_",
            ""
        )


        reset_mode(
            context
        )


        context.user_data[
            "mode"
        ] = "convert_image"


        context.user_data[
            "target_format"
        ] = target_format


        await query.edit_message_text(

            f"✅ {target_format.upper()} selected.\n\n"

            "Send the image you want to convert."
        )


        return


    mode_map = {

        "mode_scan": (

            "scan",

            "📄 Document scanner ready.\n\n"
            "Send a clear document photo."

        ),

        "mode_to_pdf": (

            "to_pdf",

            "📑 Image to PDF ready.\n\n"
            "Send an image."

        ),

        "mode_pdf_to_image": (

            "pdf_to_image",

            "📄 PDF to image ready.\n\n"
            "Send a PDF.\n\n"
            "Each page will be returned "
            "as a separate PNG file."

        ),

        "mode_to_mp3": (

            "to_mp3",

            "🎵 Audio → MP3 ready.\n\n"
            "Send an audio file, public YouTube link, "
            "or public TikTok link."

        ),

        "mode_to_mp4": (

            "to_mp4",

            "🎬 Video → MP4 ready.\n\n"
            "Send a video file, public YouTube link, "
            "or public TikTok link."

        )

    }


    if data in mode_map:

        mode, message = mode_map[
            data
        ]


        reset_mode(
            context
        )


        context.user_data[
            "mode"
        ] = mode


        await query.edit_message_text(
            message
        )


        return


    if data == "cancel_mode":

        reset_mode(
            context
        )


        await query.edit_message_text(

            "❌ Current task cancelled.\n\n"

            "Choose another tool:",

            reply_markup=main_menu_keyboard()

        )


async def process_file(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    file_id,
    filename,
    file_size=None
):

    mode = context.user_data.get(
        "mode"
    )


    if not mode:

        await update.message.reply_text(

            "Please choose a tool first.\n\n"
            "Use /start."
        )


        return


    if (

        file_size is not None

        and file_size > MAX_DOWNLOAD_SIZE

    ):

        reset_mode(
            context
        )


        await update.message.reply_text(

            "❌ This file is too large.\n\n"

            "Telegram bots currently have a "
            "20 MB download limit."
        )


        return


    await update.message.reply_text(

        "📥 File received.\n\n"
        "⚙️ Processing..."
    )


    safe_filename = os.path.basename(
        filename
    )


    input_path = os.path.join(

        INCOMING_DIR,

        safe_filename

    )


    try:

        telegram_file = (
            await context.bot.get_file(
                file_id
            )
        )


        await telegram_file.download_to_drive(

            custom_path=input_path

        )


        if mode == "scan":

            result = await asyncio.to_thread(

                scan_document,

                input_path

            )


            output_path = result[
                "pdf"
            ]


            if result["detected"]:

                await update.message.reply_text(

                    "✅ Document detected "
                    "and corrected."
                )

            else:

                await update.message.reply_text(

                    "⚠️ A clear document "
                    "boundary was not detected.\n\n"

                    "The full image was still "
                    "processed."
                )


            await send_output_file(

                update,

                output_path,

                "📄 Scanned document ready."

            )


        elif mode == "convert_image":

            target_format = (
                context.user_data.get(
                    "target_format"
                )
            )


            output_path = (
                await asyncio.to_thread(

                    convert_image,

                    input_path,

                    target_format

                )
            )


            await send_output_file(

                update,

                output_path,

                f"✅ Image converted to "
                f"{target_format.upper()}."

            )


        elif mode == "to_pdf":

            output_path = (
                await asyncio.to_thread(

                    image_to_pdf,

                    input_path

                )
            )


            await send_output_file(

                update,

                output_path,

                "✅ PDF created."

            )


        elif mode == "pdf_to_image":

            output_paths = (
                await asyncio.to_thread(

                    pdf_to_images,

                    input_path

                )
            )


            await update.message.reply_text(

                f"✅ PDF converted.\n\n"

                f"{len(output_paths)} page(s) detected.\n"

                f"Sending PNG files..."
            )


            for page_number, output_path in enumerate(

                output_paths,

                start=1

            ):

                await send_output_file(

                    update,

                    output_path,

                    f"📄 Page {page_number}"

                )


        elif mode == "to_mp3":

            output_path = (
                await asyncio.to_thread(

                    audio_to_mp3,

                    input_path

                )
            )


            await send_output_file(

                update,

                output_path,

                "✅ Audio converted to MP3."

            )


        elif mode == "to_mp4":

            output_path = (
                await asyncio.to_thread(

                    video_to_mp4,

                    input_path

                )
            )


            await send_output_file(

                update,

                output_path,

                "✅ Video converted to MP4."

            )


        else:

            raise RuntimeError(
                "Unknown processing mode."
            )


    except Exception as error:

        print(
            f"Processing error: {error}"
        )


        await update.message.reply_text(

            "❌ Processing failed.\n\n"
            f"{error}"
        )


    finally:

        reset_mode(
            context
        )


        try:

            if os.path.exists(
                input_path
            ):

                os.remove(
                    input_path
                )

        except Exception:

            pass


async def send_output_file(
    update,
    output_path,
    caption
):

    if not os.path.exists(
        output_path
    ):

        raise RuntimeError(
            "The output file was not created."
        )


    output_size = os.path.getsize(
        output_path
    )


    if output_size > MAX_UPLOAD_SIZE:

        await update.message.reply_text(

            "❌ The converted file is larger "
            "than Telegram's 50 MB upload limit."
        )


        return


    filename = os.path.basename(
        output_path
    )


    with open(
        output_path,
        "rb"
    ) as output_file:

        await update.message.reply_document(

            document=output_file,

            filename=filename,

            caption=caption

        )


async def process_media_link(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    url
):

    mode = context.user_data.get(
        "mode"
    )


    if mode not in (
        "to_mp3",
        "to_mp4"
    ):

        await update.message.reply_text(

            "Please choose "
            "🎵 Audio → MP3 or "
            "🎬 Video → MP4 first."
        )


        return


    if not is_supported_media_url(
        url
    ):

        await update.message.reply_text(

            "❌ Unsupported link.\n\n"

            "Please send a public "
            "YouTube or TikTok link."
        )


        return


    target_format = (

        "mp3"

        if mode == "to_mp3"

        else

        "mp4"

    )


    await update.message.reply_text(

        "🔗 Link received.\n\n"

        "⬇️ Downloading media...\n"

        "⚙️ Processing..."
    )


    try:

        output_path = (
            await asyncio.to_thread(

                download_media_link,

                url,

                target_format

            )
        )


        await send_output_file(

            update,

            output_path,

            (

                "✅ Audio converted to MP3."

                if target_format == "mp3"

                else

                "✅ Video converted to MP4."

            )

        )


    except Exception as error:

        print(
            f"Link processing error: {error}"
        )


        await update.message.reply_text(

            "❌ Could not process this link.\n\n"

            f"{error}"
        )


    finally:

        reset_mode(
            context
        )


async def receive_text_link(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return


    text = (
        update.message.text
        or ""
    ).strip()


    if not text:
        return


    mode = context.user_data.get(
        "mode"
    )


    if mode not in (
        "to_mp3",
        "to_mp4"
    ):

        return


    await process_media_link(

        update,

        context,

        text

    )


async def receive_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return


    if not update.message.photo:
        return


    mode = context.user_data.get(
        "mode"
    )


    if mode not in (
        "scan",
        "convert_image",
        "to_pdf"
    ):

        await update.message.reply_text(

            "❌ Please choose an image-based "
            "tool first."
        )


        return


    photo = update.message.photo[-1]


    filename = (

        f"telegram_photo_"

        f"{update.message.message_id}.jpg"

    )


    await process_file(

        update,

        context,

        photo.file_id,

        filename,

        photo.file_size

    )


async def receive_document(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return


    document = (
        update.message.document
    )


    if not document:
        return


    await process_file(

        update,

        context,

        document.file_id,

        document.file_name

        or (

            f"telegram_file_"

            f"{update.message.message_id}"

        ),

        document.file_size

    )


async def receive_audio(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return


    audio = update.message.audio


    if not audio:
        return


    mode = context.user_data.get(
        "mode"
    )


    if mode != "to_mp3":

        await update.message.reply_text(

            "Please choose "
            "🎵 Audio → MP3 first."
        )


        return


    filename = (

        audio.file_name

        or (

            f"audio_"

            f"{update.message.message_id}.audio"

        )

    )


    await process_file(

        update,

        context,

        audio.file_id,

        filename,

        audio.file_size

    )


async def receive_video(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return


    video = update.message.video


    if not video:
        return


    mode = context.user_data.get(
        "mode"
    )


    if mode != "to_mp4":

        await update.message.reply_text(

            "Please choose "
            "🎬 Video → MP4 first."
        )


        return


    filename = (

        video.file_name

        or (

            f"video_"

            f"{update.message.message_id}.mp4"

        )

    )


    await process_file(

        update,

        context,

        video.file_id,

        filename,

        video.file_size

    )


async def post_init(
    application
):

    await application.bot.set_my_commands([

        BotCommand(
            "start",
            "Show all tools"
        ),

        BotCommand(
            "scan",
            "Scan a document"
        ),

        BotCommand(
            "convert_image",
            "Convert image format"
        ),

        BotCommand(
            "to_pdf",
            "Convert image to PDF"
        ),

        BotCommand(
            "pdf_to_image",
            "Convert PDF to PNG images"
        ),

        BotCommand(
            "to_mp3",
            "Convert audio or link to MP3"
        ),

        BotCommand(
            "to_mp4",
            "Convert video or link to MP4"
        ),

        BotCommand(
            "cancel",
            "Cancel current task"
        ),

        BotCommand(
            "help",
            "Show help"
        )

    ])


def main():

    application = (

        ApplicationBuilder()

        .token(
            BOT_TOKEN
        )

        .post_init(
            post_init
        )

        .build()

    )


    application.add_handler(

        CommandHandler(
            "start",
            start
        )

    )


    application.add_handler(

        CommandHandler(
            "help",
            help_command
        )

    )


    application.add_handler(

        CommandHandler(
            "cancel",
            cancel_command
        )

    )


    application.add_handler(

        CommandHandler(
            "scan",
            scan_command
        )

    )


    application.add_handler(

        CommandHandler(
            "convert_image",
            convert_image_command
        )

    )


    application.add_handler(

        CommandHandler(
            "to_pdf",
            to_pdf_command
        )

    )


    application.add_handler(

        CommandHandler(
            "pdf_to_image",
            pdf_to_image_command
        )

    )


    application.add_handler(

        CommandHandler(
            "to_mp3",
            to_mp3_command
        )

    )


    application.add_handler(

        CommandHandler(
            "to_mp4",
            to_mp4_command
        )

    )


    application.add_handler(

        CallbackQueryHandler(
            button_callback
        )

    )


    application.add_handler(

        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive_text_link
        )

    )


    application.add_handler(

        MessageHandler(
            filters.PHOTO,
            receive_photo
        )

    )


    application.add_handler(

        MessageHandler(
            filters.AUDIO,
            receive_audio
        )

    )


    application.add_handler(

        MessageHandler(
            filters.VIDEO,
            receive_video
        )

    )


    application.add_handler(

        MessageHandler(
            filters.Document.ALL,
            receive_document
        )

    )


    print(
        "Telegram File Utility Bot is running..."
    )


    application.run_polling()


if __name__ == "__main__":

    main()
