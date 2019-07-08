import discord
import io
import sympy
from sys import exc_info
import tempfile
import messagefuncs

import matplotlib.pyplot as plt

def renderLatex(formula, fontsize=12, dpi=300, format='svg', file=None):
    """Renders LaTeX formula into image or prints to file.
    """
    plt.rc('text', usetex=True)
    plt.rc('text.latex', preamble=r'\usepackage{amsmath}')
    plt.rc('font', family='serif')
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, u'{}'.format(formula), fontsize=fontsize, verticalalignment='center_baseline', clip_on=True)
    plt.tight_layout()

    output = io.BytesIO() if file is None else file
    fig.savefig(output, dpi=dpi, transparent=False, format=format,
       bbox_inches='tight', pad_inches=None, frameon=True)

    plt.close(fig)

    if file is None:
        output.seek(0)
        return output

async def latex_render_function(message, client, args):
    try:
        renderstring = "$"+message.content.split(" ", 1)[1]+"$"
        await message.channel.send("`"+renderstring+"`", file=discord.File(renderLatex(renderstring, format='png'), filename="fletcher-render.png"))
    except RuntimeError as e:
        exc_type, exc_obj, exc_tb = exc_info()
        print("LRF[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))
        await message.add_reaction('🚫')
        await messagefuncs.sendWrappedMessage(f'Error rendering LaTeX: {e}', message.author)
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        print("LRF[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))

# Register functions in client
def autoload(ch):
    ch.add_command({
        'trigger': ['!math', '!latex'],
        'function': latex_render_function,
        'async': True,
        'args_num': 0,
        'long_run': True,
        'args_name': [],
        'description': 'Render arguments as LaTeX formula (does not require `$$`)'
        })
