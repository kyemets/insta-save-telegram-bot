from aiogram import Bot, Dispatcher, executor, types, executor
import aiogram.utils.markdown as fmt
from instaloader import Instaloader 
from tg_token import TOKEN
from insta_config import USERNAME, PASSWORD
import asyncio
import os, os.path, glob
import keyboard as kb


bot = Bot(TOKEN)
dp = Dispatcher(bot)

L = Instaloader()
L.login(USERNAME, PASSWORD)


''' Command Start '''
@dp.message_handler(commands="start")
async def cmd_start(message: types.Message):
  user_id = message.from_user.id
  await bot.send_sticker(user_id, sticker='CAACAgIAAxkBAAEEeItiWG7TWqCapeRnGLmb0JhzlfO6UwACAQEAAladvQoivp8OuMLmNCME')
  await message.answer(f"Hi, {message.from_user.first_name}")
  await message.answer("List of available commands: /help  ")


""" Download stories """
@dp.message_handler(commands="stories")
async def cmd_start(message: types.Message):
  await message.answer("Input a username or send profile link")
  URL = 'https://www.instagram.com/'

  @dp.message_handler()
  async def get_username(message: types.Message):
    get_username = message.text
    username = get_username.replace(URL, '').replace('/', '')
    print(username)
    profile = L.check_profile_id(username)
    print(profile.userid)
    await message.answer("User found, please wait... ⏳", disable_notification=True)
    
    profile = L.check_profile_id(username)
    L.download_stories(userids=[profile.userid],filename_target='{}'.format(profile.username))
    dirname = str(username)
 
    print('path: ', dirname)
    await asyncio.sleep(1)
    media = types.MediaGroup()
    await types.ChatActions.upload_photo()
    os.chdir(dirname)

    # send photo
    for file in glob.glob("*.jpg"):
      print(file)
      media.attach_photo(types.InputFile(file))
    await message.reply_media_group(media=media)
    media = types.MediaGroup()
    await types.ChatActions.upload_video()

    # send video
    for file in glob.glob("*.mp4"):
      print(file)
      media.attach_video(types.InputFile(file))
    await message.reply_media_group(media=media)


''' Get Help '''
@dp.message_handler(commands="help")
async def cmd_start(message: types.Message):
  await message.answer(
    fmt.text(
      fmt.text("/stories — get a stories"),
        sep="\n"
      ), parse_mode="HTML"
  )

  
if __name__ == '__main__':
  executor.start_polling(dp, skip_updates=True)