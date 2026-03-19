import os
import re
import io
import logging
from functools import partial
from datetime import datetime
from typing import Union, BinaryIO, List, Optional, Callable
from pyrogram import StopTransmission, enums, raw, types, utils
from pyrogram.errors import FilePartMissing
from pyrogram.file_id import FileType
from pyrogram import enums, types, Client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s ",
    force=True
)
pyro_log = logging.getLogger("pyrogram")
pyro_log.setLevel(logging.WARNING)

log = logging.getLogger(__name__)

async def custom_send_cached_media(
        self: "Client",
        chat_id: Union[int, str],
        file_id: str,
        caption: str = "",
        parse_mode: Optional["enums.ParseMode"] = None,
        caption_entities: List["types.MessageEntity"] = None,
        has_spoiler: bool = None,
        disable_notification: bool = None,
        message_thread_id: int = None,
        reply_to_message_id: int = None,
        reply_to_story_id: int = None,
        reply_to_chat_id: Union[int, str] = None,
        reply_to_monoforum_id: Union[int, str] = None,
        quote_text: str = None,
        quote_entities: List["types.MessageEntity"] = None,
        cover: Union[str, BinaryIO] = None,
        schedule_date: datetime = None,
        protect_content: bool = None,
        allow_paid_broadcast: bool = None,
        invert_media: bool = False,
        reply_markup: Union[
            "types.InlineKeyboardMarkup",
            "types.ReplyKeyboardMarkup",
            "types.ReplyKeyboardRemove",
            "types.ForceReply"
        ] = None
    ) -> Optional["types.Message"]:

        vidcover_file = None
        vidcover_media = None
        peer = await self.resolve_peer(chat_id)

        reply_to = await utils.get_reply_to(
            client=self,
            chat_id=chat_id,
            reply_to_message_id=reply_to_message_id,
            reply_to_story_id=reply_to_story_id,
            message_thread_id=message_thread_id,
            reply_to_chat_id=reply_to_chat_id,
            reply_to_monoforum_id=reply_to_monoforum_id,
            quote_text=quote_text,
            quote_entities=quote_entities,
            parse_mode=parse_mode
        )

        try:
            if cover is not None:
                if isinstance(cover, str):
                    if os.path.isfile(cover):
                        vidcover_media = await self.invoke(
                            raw.functions.messages.UploadMedia(
                                peer=peer,
                                media=raw.types.InputMediaUploadedPhoto(
                                    file=await self.save_file(cover)
                                )
                            )
                        )
                    elif re.match("^https?://", cover):
                        vidcover_media = await self.invoke(
                            raw.functions.messages.UploadMedia(
                                peer=peer,
                                media=raw.types.InputMediaPhotoExternal(
                                    url=cover
                                )
                            )
                        )
                    else:
                        vidcover_file = utils.get_input_media_from_file_id(cover, FileType.PHOTO).id
                else:
                    vidcover_media = await self.invoke(
                        raw.functions.messages.UploadMedia(
                            peer=peer,
                            media=raw.types.InputMediaUploadedPhoto(
                                file=await self.save_file(cover)
                            )
                        )
                    )

                if vidcover_media:
                    vidcover_file = raw.types.InputPhoto(
                        id=vidcover_media.photo.id,
                        access_hash=vidcover_media.photo.access_hash,
                        file_reference=vidcover_media.photo.file_reference
                    )
        except Exception as e:
            pass

        media = utils.get_input_media_from_file_id(file_id)
        if vidcover_file is not None:
            try:
                media.video_cover = vidcover_file
            except Exception as e:
                pass
        media.spoiler = has_spoiler

        r = await self.invoke(
            raw.functions.messages.SendMedia(
                peer=await self.resolve_peer(chat_id),
                media=media,
                silent=disable_notification or None,
                reply_to=reply_to,
                random_id=self.rnd_id(),
                schedule_date=utils.datetime_to_timestamp(schedule_date),
                noforwards=protect_content,
                allow_paid_floodskip=allow_paid_broadcast,
                invert_media=invert_media,
                reply_markup=await reply_markup.write(self) if reply_markup else None,
                **await utils.parse_text_entities(self, caption, parse_mode, caption_entities)
            )
        )

        for i in r.updates:
            if isinstance(i, (raw.types.UpdateNewMessage,
                              raw.types.UpdateNewChannelMessage,
                              raw.types.UpdateNewScheduledMessage)):
                return await types.Message._parse(
                    self, i.message,
                    {i.id: i for i in r.users},
                    {i.id: i for i in r.chats},
                    is_scheduled=isinstance(i, raw.types.UpdateNewScheduledMessage)
                )

async def custom_send_video(
        self: "Client",
        chat_id: Union[int, str],
        video: Union[str, BinaryIO],
        caption: str = "",
        parse_mode: Optional["enums.ParseMode"] = None,
        caption_entities: List["types.MessageEntity"] = None,
        has_spoiler: bool = None,
        ttl_seconds: int = None,
        duration: int = 0,
        width: int = 0,
        height: int = 0,
        thumb: Union[str, BinaryIO] = None,
        file_name: str = None,
        supports_streaming: bool = True,
        disable_notification: bool = None,
        message_thread_id: int = None,
        business_connection_id: str = None,
        reply_to_message_id: int = None,
        reply_to_story_id: int = None,
        reply_to_chat_id: Union[int, str] = None,
        reply_to_monoforum_id: Union[int, str] = None,
        quote_text: str = None,
        quote_entities: List["types.MessageEntity"] = None,
        cover: Union[str, BinaryIO] = None,
        start_timestamp: int = None,
        schedule_date: datetime = None,
        protect_content: bool = None,
        allow_paid_broadcast: bool = None,
        message_effect_id: int = None,
        view_once: bool = None,
        invert_media: bool = None,
        reply_markup: Union[
            "types.InlineKeyboardMarkup",
            "types.ReplyKeyboardMarkup",
            "types.ReplyKeyboardRemove",
            "types.ForceReply"
        ] = None,
        progress: Callable = None,
        progress_args: tuple = ()
    ) -> Optional["types.Message"]:

        file = None
        vidcover_file = None
        vidcover_media = None
        peer = await self.resolve_peer(chat_id)

        reply_to = await utils.get_reply_to(
            client=self,
            chat_id=chat_id,
            reply_to_message_id=reply_to_message_id,
            reply_to_story_id=reply_to_story_id,
            message_thread_id=message_thread_id,
            reply_to_chat_id=reply_to_chat_id,
            reply_to_monoforum_id=reply_to_monoforum_id,
            quote_text=quote_text,
            quote_entities=quote_entities,
            parse_mode=parse_mode
        )
        try:
            if cover is not None:
                if isinstance(cover, str):
                    if os.path.isfile(cover):
                        vidcover_media = await self.invoke(
                            raw.functions.messages.UploadMedia(
                                peer=peer,
                                media=raw.types.InputMediaUploadedPhoto(
                                    file=await self.save_file(cover)
                                )
                            )
                        )
                    elif re.match("^https?://", cover):
                        vidcover_media = await self.invoke(
                            raw.functions.messages.UploadMedia(
                                peer=peer,
                                media=raw.types.InputMediaPhotoExternal(
                                    url=cover
                                )
                            )
                        )
                    else:
                        vidcover_file = utils.get_input_media_from_file_id(cover, FileType.PHOTO).id
                else:
                    vidcover_media = await self.invoke(
                        raw.functions.messages.UploadMedia(
                            peer=peer,
                            media=raw.types.InputMediaUploadedPhoto(
                                file=await self.save_file(cover)
                            )
                        )
                    )

                if vidcover_media:
                    vidcover_file = raw.types.InputPhoto(
                        id=vidcover_media.photo.id,
                        access_hash=vidcover_media.photo.access_hash,
                        file_reference=vidcover_media.photo.file_reference
                    )

            if isinstance(video, str):
                if os.path.isfile(video):
                    thumb = await self.save_file(thumb)
                    file = await self.save_file(video, progress=progress, progress_args=progress_args)
                    media = raw.types.InputMediaUploadedDocument(
                        mime_type=self.guess_mime_type(video) or "video/mp4",
                        file=file,
                        ttl_seconds=(1 << 31) - 1 if view_once else ttl_seconds,
                        spoiler=has_spoiler,
                        thumb=thumb,
                        attributes=[
                            raw.types.DocumentAttributeVideo(
                                supports_streaming=supports_streaming or None,
                                duration=duration,
                                w=width,
                                h=height
                            ),
                            raw.types.DocumentAttributeFilename(file_name=file_name or os.path.basename(video))
                        ],
                        video_cover=vidcover_file,
                        video_timestamp=start_timestamp
                    )
                elif re.match("^https?://", video):
                    media = raw.types.InputMediaDocumentExternal(
                        url=video,
                        ttl_seconds=(1 << 31) - 1 if view_once else ttl_seconds,
                        spoiler=has_spoiler,
                        video_cover=vidcover_file,
                        video_timestamp=start_timestamp
                    )
                else:
                    media = utils.get_input_media_from_file_id(video, FileType.VIDEO, ttl_seconds=(1 << 31) - 1 if view_once else ttl_seconds)
                    if vidcover_file is not None:
                        try:
                            media.video_cover = vidcover_file
                        except Exception as e:
                            pass
                    media.spoiler = has_spoiler
            else:
                thumb = await self.save_file(thumb)
                file = await self.save_file(video, progress=progress, progress_args=progress_args)
                media = raw.types.InputMediaUploadedDocument(
                    mime_type=self.guess_mime_type(file_name or video.name) or "video/mp4",
                    file=file,
                    ttl_seconds=(1 << 31) - 1 if view_once else ttl_seconds,
                    spoiler=has_spoiler,
                    thumb=thumb,
                    attributes=[
                        raw.types.DocumentAttributeVideo(
                            supports_streaming=supports_streaming or None,
                            duration=duration,
                            w=width,
                            h=height
                        ),
                        raw.types.DocumentAttributeFilename(file_name=file_name or video.name)
                    ],
                    video_cover=vidcover_file,
                    video_timestamp=start_timestamp
                )

            while True:
                try:
                    rpc = raw.functions.messages.SendMedia(
                        peer=peer,
                        media=media,
                        silent=disable_notification or None,
                        reply_to=reply_to,
                        random_id=self.rnd_id(),
                        schedule_date=utils.datetime_to_timestamp(schedule_date),
                        noforwards=protect_content,
                        allow_paid_floodskip=allow_paid_broadcast,
                        effect=message_effect_id,
                        invert_media=invert_media,
                        reply_markup=await reply_markup.write(self) if reply_markup else None,
                        **await utils.parse_text_entities(self, caption, parse_mode, caption_entities)
                    )
                    if business_connection_id is not None:
                        r = await self.invoke(
                            raw.functions.InvokeWithBusinessConnection(
                                connection_id=business_connection_id,
                                query=rpc
                            )
                        )
                    else:
                        r = await self.invoke(rpc)
                except FilePartMissing as e:
                    await self.save_file(video, file_id=file.id, file_part=e.value)
                else:
                    for i in r.updates:
                        if isinstance(i, (raw.types.UpdateNewMessage,
                                          raw.types.UpdateNewChannelMessage,
                                          raw.types.UpdateNewScheduledMessage,
                                          raw.types.UpdateBotNewBusinessMessage)):
                            return await types.Message._parse(
                                self, i.message,
                                {i.id: i for i in r.users},
                                {i.id: i for i in r.chats},
                                is_scheduled=isinstance(i, raw.types.UpdateNewScheduledMessage),
                                business_connection_id=business_connection_id
                            )
        except StopTransmission:
            return None


async def custom_copy(
    self: "types.Message",
    chat_id: Union[int, str],
    caption: str = None,
    parse_mode: Optional["enums.ParseMode"] = None,
    caption_entities: list["types.MessageEntity"] = None,
    has_spoiler: bool = None,
    video_cover: Optional[Union[str, "io.BytesIO"]] = None,
    disable_notification: bool = None,
    message_thread_id: int = None,
    quote_text: str = None,
    quote_entities: List["types.MessageEntity"] = None,
    reply_to_message_id: int = None,
    reply_to_chat_id: int = None,
    schedule_date: datetime = None,
    protect_content: bool = None,
    allow_paid_broadcast: bool = None,
    invert_media: bool = None,
    reply_markup: Union[
        "types.InlineKeyboardMarkup",
        "types.ReplyKeyboardMarkup",
        "types.ReplyKeyboardRemove",
        "types.ForceReply"
    ] = object
) -> Union["types.Message", List["types.Message"]]:

    if self.service:
        log.warning("Service messages cannot be copied. chat_id: %s, message_id: %s",
                    self.chat.id, self.id)
    elif self.game and not await self._client.storage.is_bot():
        log.warning("Users cannot send messages with Game media type. chat_id: %s, message_id: %s",
                    self.chat.id, self.id)
    elif self.empty:
        log.warning("Empty messages cannot be copied.")
    elif self.text:
        return await self._client.send_message(
            chat_id,
            text=self.text,
            entities=self.entities,
            parse_mode=enums.ParseMode.DISABLED,
            disable_web_page_preview=not self.web_page_preview,
            disable_notification=disable_notification,
            message_thread_id=message_thread_id,
            reply_to_message_id=reply_to_message_id,
            reply_to_chat_id=reply_to_chat_id,
            quote_text=quote_text,
            quote_entities=quote_entities,
            schedule_date=schedule_date,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            reply_markup=self.reply_markup if reply_markup is object else reply_markup
        )
    elif self.media:
        send_media = partial(
            self._client.send_cached_media,
            chat_id=chat_id,
            disable_notification=disable_notification,
            message_thread_id=message_thread_id,
            reply_to_message_id=reply_to_message_id,
            reply_to_chat_id=reply_to_chat_id,
            schedule_date=schedule_date,
            has_spoiler=has_spoiler,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            invert_media=invert_media,
            reply_markup=self.reply_markup if reply_markup is object else reply_markup
        )

        if self.photo:
            file_id = self.photo.file_id
        elif self.audio:
            file_id = self.audio.file_id
        elif self.document:
            file_id = self.document.file_id
        elif self.video:
            return await self._client.send_video(
                chat_id,
                video=self.video.file_id,
                caption=caption,
                parse_mode=parse_mode,
                caption_entities=caption_entities,
                invert_media=invert_media or self.invert_media,
                cover=video_cover,
                has_spoiler=self.has_media_spoiler,
                disable_notification=disable_notification,
                protect_content=self.has_protected_content if protect_content is None else protect_content,
                allow_paid_broadcast=allow_paid_broadcast,
                message_thread_id=self.message_thread_id if message_thread_id is None else message_thread_id,
                reply_markup=self.reply_markup if reply_markup is object else reply_markup,
                schedule_date=schedule_date,
                reply_to_message_id=reply_to_message_id
            )
        elif self.animation:
            file_id = self.animation.file_id
        elif self.voice:
            file_id = self.voice.file_id
        elif self.sticker:
            file_id = self.sticker.file_id
        elif self.video_note:
            file_id = self.video_note.file_id
        elif self.contact:
            return await self._client.send_contact(
                chat_id,
                phone_number=self.contact.phone_number,
                first_name=self.contact.first_name,
                last_name=self.contact.last_name,
                vcard=self.contact.vcard,
                disable_notification=disable_notification,
                message_thread_id=message_thread_id,
                schedule_date=schedule_date,
                allow_paid_broadcast=allow_paid_broadcast,
            )
        elif self.location:
            return await self._client.send_location(
                chat_id,
                latitude=self.location.latitude,
                longitude=self.location.longitude,
                disable_notification=disable_notification,
                message_thread_id=message_thread_id,
                schedule_date=schedule_date,
                allow_paid_broadcast=allow_paid_broadcast
            )
        elif self.venue:
            return await self._client.send_venue(
                chat_id,
                latitude=self.venue.location.latitude,
                longitude=self.venue.location.longitude,
                title=self.venue.title,
                address=self.venue.address,
                foursquare_id=self.venue.foursquare_id,
                foursquare_type=self.venue.foursquare_type,
                disable_notification=disable_notification,
                message_thread_id=message_thread_id,
                schedule_date=schedule_date,
                allow_paid_broadcast=allow_paid_broadcast
            )
        elif self.poll:
            return await self._client.send_poll(
                chat_id,
                question=self.poll.question,
                options=[
                    types.PollOption(
                        text=opt.text,
                        entities=opt.entities
                    ) for opt in self.poll.options
                ],
                disable_notification=disable_notification,
                message_thread_id=message_thread_id,
                schedule_date=schedule_date,
                allow_paid_broadcast=allow_paid_broadcast
            )
        elif self.game:
            return await self._client.send_game(
                chat_id,
                game_short_name=self.game.short_name,
                disable_notification=disable_notification,
                message_thread_id=message_thread_id,
                allow_paid_broadcast=allow_paid_broadcast
            )
        elif self.web_page_preview:
            return await self._client.send_web_page(
                chat_id,
                url=self.web_page_preview.webpage.url,
                text=self.text,
                entities=self.entities,
                parse_mode=enums.ParseMode.DISABLED,
                large_media=self.web_page_preview.force_large_media,
                invert_media=self.web_page_preview.invert_media,
                disable_notification=disable_notification,
                message_thread_id=message_thread_id,
                reply_to_message_id=reply_to_message_id,
                reply_to_chat_id=reply_to_chat_id,
                quote_text=quote_text,
                quote_entities=quote_entities,
                schedule_date=schedule_date,
                protect_content=protect_content,
                allow_paid_broadcast=allow_paid_broadcast,
                reply_markup=self.reply_markup if reply_markup is object else reply_markup
            )
        else:
            raise ValueError("Unknown media type")

        if self.sticker or self.video_note:
            return await send_media(
                file_id=file_id,
                message_thread_id=message_thread_id,
                allow_paid_broadcast=allow_paid_broadcast
            )
        else:
            if caption is None:
                caption = self.caption or ""
                caption_entities = self.caption_entities

            return await send_media(
                file_id=file_id,
                caption=caption,
                parse_mode=parse_mode,
                caption_entities=caption_entities,
                has_spoiler=has_spoiler,
                message_thread_id=message_thread_id,
                allow_paid_broadcast=allow_paid_broadcast
            )
    else:
        raise ValueError("Can't copy this message")


async def custom_copy_message(
    self: "Client",
    chat_id: Union[int, str],
    from_chat_id: Union[int, str],
    message_id: int,
    caption: str = None,
    parse_mode: Optional["enums.ParseMode"] = None,
    caption_entities: List["types.MessageEntity"] = None,
    has_spoiler: bool = None,
    disable_notification: bool = None,
    message_thread_id: int = None,
    reply_to_message_id: int = None,
    reply_to_chat_id: int = None,
    schedule_date: datetime = None,
    protect_content: bool = None,
    allow_paid_broadcast: bool = None,
    invert_media: bool = False,
    video_cover: Optional[Union[str, "io.BytesIO"]] = None,
    reply_markup: Union[
        "types.InlineKeyboardMarkup",
        "types.ReplyKeyboardMarkup",
        "types.ReplyKeyboardRemove",
        "types.ForceReply"
    ] = None
) -> "types.Message":

    message: types.Message = await self.get_messages(from_chat_id, message_id)


    return await message.copy(
        chat_id=chat_id,
        caption=caption,
        parse_mode=parse_mode,
        caption_entities=caption_entities,
        has_spoiler=has_spoiler,
        video_cover=video_cover,
        disable_notification=disable_notification,
        message_thread_id=message_thread_id,
        reply_to_message_id=reply_to_message_id,
        reply_to_chat_id=reply_to_chat_id,
        schedule_date=schedule_date,
        protect_content=protect_content,
        allow_paid_broadcast=allow_paid_broadcast,
        invert_media=invert_media,
        reply_markup=reply_markup
    )



Client.send_cached_media = custom_send_cached_media
Client.send_video = custom_send_video
types.Message.copy = custom_copy
Client.copy_message = custom_copy_message


log.info("Custom Pyrogram methods have been applied.")
