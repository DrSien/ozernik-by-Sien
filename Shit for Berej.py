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
            
@bot.tree.command(name='войсмастер', description='Установить канал из которого создаётся войс')
@discord.app_commands.rename(voice = 'канал', role = 'роль')
@discord.app_commands.describe(voice = 'Исходный канал из которого создаются другие', role = 'Роль, которой можно менять название созданного канала')
async def CV_settings(interaction: discord.Interaction, voice: discord.VoiceChannel, role: discord.Role):
    if interaction.user.guild_permissions.administrator == True:
        print(voice)
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
                print(rename_role_id)
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
def check_lvl(con, r):# [0]uid [1]exp [2]lvl
    uid = r[0]
    defult_lvl = 10
    if r[2] == 0:
        if r[1] >= defult_lvl:
            new_lvl = r[2]+1
            con.execute(f"UPDATE level SET lvl = {new_lvl} WHERE uid={uid}")
    else:
        if r[1] >= defult_lvl*1.3**r[2]:
            new_lvl = r[2]+1
            con.execute(f"UPDATE level SET lvl = {new_lvl} WHERE uid={uid}")
@bot.event #Триггер сообщений
async def on_message(message):
    con = open_lvl_base(message.guild)
    try:
        r = con.execute(f"SELECT * FROM level WHERE uid={message.author.id}").fetchone()
        r = r[1]+1
        print(r)
        con.execute(f"UPDATE level SET exp = {r} WHERE uid={message.author.id}")
        check_lvl(con, con.execute(f"SELECT * FROM level WHERE uid={message.author.id}").fetchone())
    except:
        con.execute(f"INSERT INTO level (uid) VALUES ({message.author.id})")
        print('пользователь добавлен')
    finally:
        con.commit()

async def on_ready():
    await bot.tree.sync()
bot.run('MTIyNzU3MzEyNTU3MTU0MzE0Mg.GpIbyx.X8ebJ-K4OC3HLWFLhpXvdXTeC2XY5akHxCIV9E')