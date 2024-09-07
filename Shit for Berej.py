import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='.', intents=intents)


# Создание войса
voice_list = [] #Список созданных каналов
@bot.event
async def on_voice_state_update(member, before, after):
    try:
        with open(f'CVid {member.guild.name}.txt', 'r') as f:
            creator_voice_id = int(f.readlines()[0][:-1])
        try:
            if (not before.channel.members) and (before.channel.id in voice_list):
                await before.channel.delete()
                voice_list.remove(before.channel.id)
            if after.channel.id == creator_voice_id:
                channel = await member.guild.create_voice_channel(name = f'Канал {member.display_name}', category = member.voice.channel.category)
                await channel.send('Используйте `/rename` для смены названия голосового канала')
                voice_list.append(channel.id)
                await member.move_to(channel)
        except:
            if after.channel.id == creator_voice_id:
                channel = await member.guild.create_voice_channel(name = f'Канал {member.display_name}', category = member.voice.channel.category)
                await channel.send('Используйте `/rename` для смены названия голосового канала')
                voice_list.append(channel.id)
                await member.move_to(channel)
    except:
        if (not before.channel.members) and (before.channel.id in voice_list):
            await before.channel.delete()
            voice_list.remove(before.channel.id)
            
@bot.tree.command(name='войскреатор', description='Установить канал из которого создаётся войс')
@discord.app_commands.rename(voice = 'канал', role = 'роль')
@discord.app_commands.describe(voice = 'Исходный канал из которого создаются другие', role = 'Роль, которой можно менять название созданного канала')
async def CV_settings(interaction: discord.Interaction, voice: discord.VoiceChannel, role: discord.Role):
    if interaction.user.guild_permissions.administrator == True:
        with open(f'CVid {interaction.guild.name}.txt', 'w') as f:
            f.writelines('%d' % voice.id +'\n'+ '%d' % role.id)
        await interaction.response.send_message(f'Теперь при подключении к {voice.mention} будет создаваться новый канал\nУчастники с ролью {role.mention} смогут менять название созданного канала')
    else:
        await interaction.response.send_message('У вас недостаточно прав чтобы использовать эту команду', ephemeral=True)
        

@bot.tree.command(name='rename', description='Меняет название голосового канала')
@discord.app_commands.rename(new_name = 'название')
@discord.app_commands.describe(new_name = 'Новое название канала')
async def rename_voice(interaction: discord.Interaction, new_name:str):
    try:
        with open(f'CVid {interaction.guild.name}.txt', 'r') as f:
                rename_role_id = int(f.readlines()[1])
        if interaction.guild.get_role(rename_role_id) in interaction.user.roles:
            if interaction.channel.id in voice_list:
                await interaction.channel.edit(name = new_name)
                await interaction.response.send_message(f'{interaction.user.display_name} меняет название канала на **{new_name}**')
            else:
                await interaction.response.send_message('Нельзя изменить название этого канала', ephemeral=True)
        else:
            await interaction.response.send_message(f'Изменить название канала может только {interaction.guild.get_role(rename_role_id).mention}',ephemeral=True)
    except:
        await interaction.response.send_message('Эта команда ещё не настроена', ephemeral=True)


# Опыт из сообщений
def open_lvl_base(guild):
    con = sqlite3.connect(f"base {guild}.db")
    con.execute('''CREATE TABLE IF NOT EXISTS level (
"uid"	INTEGER,
"exp"	INTEGER DEFAULT 0,
"lvl"	INTEGER DEFAULT 0
)''')
    return con
def check_lvl(guild, con, r):# [0]uid [1]exp [2]lvl
    uid = r[0]
    defult_lvl = sqlite3.connect(f"base {guild}.db").execute('SELECT "d lvl" FROM "XP settings"').fetchone()[0]
    if r[2] == 0:
        if r[1] >= defult_lvl:
            new_lvl = r[2]+1
            con.execute(f"UPDATE level SET lvl = {new_lvl} WHERE uid={uid}")
    else:
        if r[1] >= defult_lvl*1.3**r[2]:
            new_lvl = r[2]+1
            con.execute(f"UPDATE level SET lvl = {new_lvl} WHERE uid={uid}")
def on_bl(guild):#чёрный список. возвращает список каналов
    con = sqlite3.connect(f'base {guild}.db')
    con.execute('''CREATE TABLE IF NOT EXISTS "blacklist" ("channel" INTEGER, "role"	INTEGER)''')
    con.row_factory = lambda cursor, row: row[0]
    return (con.cursor().execute('SELECT "channel" FROM blacklist').fetchall(), con.cursor().execute('SELECT "role" FROM blacklist').fetchall())
#def on_multi(guild):

def check_role(message):#проверяет роль в чс
    for role in on_bl(message.guild)[1]:
        if message.guild.get_role(role) in message.author.roles:
            return False

def add_xp(guild, uid, characters):#считает сколько опыта добавть в зависимости от кол-ва символов в сообщении (просьба берджа)
    con = sqlite3.connect(f"base {guild}.db")
    k = con.execute(f'SELECT "ch k" FROM "XP settings"').fetchone()[0]
    con.close()
    con2 = open_lvl_base(guild)
    lvl = con2.execute(f'SELECT lvl FROM level WHERE uid = {uid}').fetchone()[0]
    con2.close()
    defult_lvl = sqlite3.connect(f"base {guild}.db").execute('SELECT "d lvl" FROM "XP settings"').fetchone()[0]
    cap = defult_lvl*1.3**lvl
    return int(max(1, min(characters/k, cap-1)))

@bot.event #Триггер сообщений
async def on_message(message):
    if not message.author.bot:
        if (message.channel.id not in on_bl(message.guild)[0]):
            if not check_role(message):
                con = open_lvl_base(message.guild)
                try:
                    r = con.execute(f"SELECT * FROM level WHERE uid={message.author.id}").fetchone()
                    r = r[1] + add_xp(message.guild, message.author.id, len(message.content))
                    con.execute(f"UPDATE level SET exp = {r} WHERE uid={message.author.id}")
                    check_lvl(message.guild, con, con.execute(f"SELECT * FROM level WHERE uid={message.author.id}").fetchone())
                except:
                    con.execute(f"INSERT INTO level (uid) VALUES ({message.author.id})")
                finally:
                    con.commit()

#Команды для настройки
@bot.tree.command(name='blacklist', description='Посмотреть или изменить чёрный список')#чёрный список
@discord.app_commands.rename(channel = 'канал', role = 'роль')
@discord.app_commands.describe(channel = 'Добавить или удалить канал', role = 'Добавить или удалить роль')
async def bl(interction:discord.Interaction, channel:typing.Optional[discord.TextChannel], role:typing.Optional[discord.Role]):
        if channel == None and role == None:
            bl_embed = discord.Embed(title='Чёрный список', color=discord.Colour.red())
            bl_list = on_bl(interction.guild)
            if bl_list[0]:
                bl_embed.add_field(name='Каналы в чёрном списке:', value='\n'.join(str(bot.get_channel(x).mention) for x in bl_list[0] if x != None))
            if bl_list[1]:
                bl_embed.add_field(name='Роли в чёрном списке:', value='\n'.join(str(interction.guild.get_role(x).mention) for x in bl_list[1] if x != None))
            await interction.response.send_message(embed=bl_embed)
        elif channel != None and role == None:
            if channel.id not in on_bl(interction.guild)[0]:
                con = sqlite3.connect(f'base {interction.guild}.db')
                con.execute(f'INSERT INTO blacklist (channel) VALUES ({channel.id})')
                con.commit()
                con.close()
                await interction.response.send_message(f'Добавлено в чёрный список: {channel.mention}')
            else:
                con = sqlite3.connect(f'base {interction.guild}.db')
                con.execute(f'DELETE FROM blacklist WHERE channel = {channel.id}')
                con.commit()
                con.close()
                await interction.response.send_message(f'Удалено из чёроного списка: {channel.mention}')
        elif role != None and channel == None:
            if role.id not in on_bl(interction.guild)[1]:
                con = sqlite3.connect(f'base {interction.guild}.db')
                con.execute(f'INSERT INTO blacklist (role) VALUES ({role.id})')
                con.commit()
                con.close()
                await interction.response.send_message(f'Добавлено в чёрный список: {role.mention}')
            else:
                con = sqlite3.connect(f'base {interction.guild}.db')
                con.execute(f'DELETE FROM blacklist WHERE role = {role.id}')
                con.commit()
                con.close()
                await interction.response.send_message(f'Удалено из чёрного списка: {role.mention}')
        else:
            resp = 'Изменения в чёрном списке:\n'
            if channel.id not in on_bl(interction.guild)[0]:
                con = sqlite3.connect(f'base {interction.guild}.db')
                con.execute(f'INSERT INTO blacklist (channel) VALUES ({channel.id})')
                con.commit()
                con.close()
                resp += f'{channel.mention} - добавлено\n'
            else:
                con = sqlite3.connect(f'base {interction.guild}.db')
                con.execute(f'DELETE FROM blacklist WHERE channel = {channel.id}')
                con.commit()
                con.close()
                resp += f'{channel.mention} - удалено\n'
            if role.id not in on_bl(interction.guild)[1]:
                con = sqlite3.connect(f'base {interction.guild}.db')
                con.execute(f'INSERT INTO blacklist (role) VALUES ({role.id})')
                con.commit()
                con.close()
                resp += f'{role.mention} - добавлено'
            else:
                con = sqlite3.connect(f'base {interction.guild}.db')
                con.execute(f'DELETE FROM blacklist WHERE role = {role.id}')
                con.commit()
                con.close()
                resp +=f'{role.mention} - удалено'
            await interction.response.send_message(resp)

async def on_ready():
    await bot.tree.sync()
