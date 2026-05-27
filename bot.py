import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime

# =============================================
# El TOKEN y CANAL_ID se leen desde variables
# de entorno (configuradas en Railway)
# =============================================
TOKEN = os.environ["DISCORD_TOKEN"]
CANAL_CUMPLES_ID = int(os.environ["CANAL_ID"])
# =============================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

ARCHIVO = "cumpleanos.json"

def cargar_datos():
    if not os.path.exists(ARCHIVO):
        return {}
    with open(ARCHIVO, "r") as f:
        return json.load(f)

def guardar_datos(datos):
    with open(ARCHIVO, "w") as f:
        json.dump(datos, f, indent=2)


@tasks.loop(hours=24)
async def revisar_cumpleanos():
    ahora = datetime.now()
    if ahora.hour != 9:
        return

    canal = bot.get_channel(CANAL_CUMPLES_ID)
    if not canal:
        return

    datos = cargar_datos()
    hoy = ahora.strftime("%d/%m")

    for user_id, fecha in datos.items():
        if fecha == hoy:
            try:
                miembro = await canal.guild.fetch_member(int(user_id))
                await canal.send(
                    f"🎂 ¡Hoy es el cumpleaños de {miembro.mention}! "
                    f"¡Feliz cumpleaños! 🎉🎊"
                )
            except Exception:
                pass


@revisar_cumpleanos.before_loop
async def antes_del_loop():
    await bot.wait_until_ready()


@bot.command(name="cumple")
async def registrar_cumple(ctx, fecha: str = None):
    if fecha is None:
        await ctx.send("❌ Debes indicar tu fecha. Ejemplo: `!cumple 25/07`")
        return
    try:
        datetime.strptime(fecha, "%d/%m")
    except ValueError:
        await ctx.send("❌ Formato incorrecto. Usa `!cumple DD/MM` — ejemplo: `!cumple 25/07`")
        return
    datos = cargar_datos()
    datos[str(ctx.author.id)] = fecha
    guardar_datos(datos)
    await ctx.send(f"✅ ¡Listo, {ctx.author.mention}! Tu cumpleaños ({fecha}) fue registrado. 🎂")


@bot.command(name="micumple")
async def mi_cumple(ctx):
    datos = cargar_datos()
    user_id = str(ctx.author.id)
    if user_id not in datos:
        await ctx.send("No tengo tu cumpleaños registrado. Usa `!cumple DD/MM` para añadirlo.")
    else:
        await ctx.send(f"🎂 Tu cumpleaños está registrado para el **{datos[user_id]}**.")


@bot.command(name="cumples")
async def ver_cumples(ctx):
    datos = cargar_datos()
    if not datos:
        await ctx.send("Aún no hay cumpleaños registrados. Usa `!cumple DD/MM` para añadir el tuyo.")
        return
    ordenados = sorted(datos.items(), key=lambda x: (x[1][3:], x[1][:2]))
    lines = ["🎂 **Cumpleaños del servidor:**\n"]
    for user_id, fecha in ordenados:
        try:
            miembro = await ctx.guild.fetch_member(int(user_id))
            nombre = miembro.display_name
        except Exception:
            nombre = f"Usuario {user_id}"
        lines.append(f"• **{fecha}** — {nombre}")
    await ctx.send("\n".join(lines))


@bot.command(name="borrarcumple")
@commands.has_permissions(administrator=True)
async def borrar_cumple(ctx, miembro: discord.Member):
    datos = cargar_datos()
    user_id = str(miembro.id)
    if user_id in datos:
        del datos[user_id]
        guardar_datos(datos)
        await ctx.send(f"✅ Cumpleaños de {miembro.mention} eliminado.")
    else:
        await ctx.send("No tenía ningún cumpleaños registrado.")


@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")
    revisar_cumpleanos.start()


bot.run(TOKEN)
