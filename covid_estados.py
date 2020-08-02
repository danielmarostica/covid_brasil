# -*- coding: utf-8 -*-
# Python 3.5+
# Requer ImageMagick para renderizar a animação
import pandas as pd
import numpy as np
import os, subprocess
import matplotlib.pyplot as plt
from datetime import datetime
from mpl_toolkits.axes_grid1.inset_locator import InsetPosition
from matplotlib.offsetbox import OffsetImage, AnnotationBbox, TextArea
from matplotlib import rc
from pathlib import Path

'''
Faça download dos dados em https://covid.saude.gov.br;
Salve o arquivo .xlsx como .csv (o desempenho é muito superior ao importar dados nesse formato) no diretório deste script;
A animação .gif será gerada automaticamente.
'''

rc('font',**{'family':'serif','serif':['Barrels']})
rc('text', usetex=True)

# cria diretório para as figuras
Path("figs").mkdir(exist_ok=True)

# importa os dados
CSV = 'arquivo_geral.csv'
dados = pd.read_csv(CSV, delimiter=',')

# limpeza, conversões e cálculos
dados_estados = dados.loc[(dados['regiao']!='Brasil') & pd.isna(dados['municipio']) & pd.notna(dados['populacaoTCU2019'])]
dados_estados['populacaoTCU2019'] = pd.to_numeric(dados_estados['populacaoTCU2019'], errors='raise')
dados_estados['per_mil'] = 1000*dados_estados['casosAcumulado']/dados_estados['populacaoTCU2019']

# colunas do csv que não serão utilizadas
dados_estados.drop(['municipio', 'coduf', 'codmun', 'codRegiaoSaude', 'semanaEpi', 'casosNovos', 'obitosNovos', 'emAcompanhamentoNovos', 'nomeRegiaoSaude', 'interior/metropolitana'], axis=1, inplace=True)

# cores
dados_estados['color'] = dados_estados['estado'].map({'RO': '#006400', 
                                                      'AC': '#008000', 
                                                      'AM': '#228B22',
                                                      'RR': '#32CD32',
                                                      'PA': '#7FFF00',
                                                      'AP': '#7CFC00',
                                                      'TO': '#00FF00',
                                                      'MA': '#999900',
                                                      'PI': '#666600',
                                                      'CE': '#999900',
                                                      'RN': '#CCCC00',
                                                      'PB': '#FFFF00',
                                                      'PE': '#FFFF33',
                                                      'AL': '#FFFF66',
                                                      'SE': '#FFFF33',
                                                      'BA': '#CCCC00',
                                                      'MG': '#FF0000',
                                                      'ES': '#8B0000',
                                                      'RJ': '#B22222',
                                                      'SP': '#DC143C',
                                                      'PR': '#00008B',
                                                      'SC': '#0000CD',
                                                      'RS': '#4169E1',
                                                      'MS': '#696969',
                                                      'MT': '#808080',
                                                      'GO': '#A9A9A9',
                                                      'DF': '#C0C0C0'})

# converte data para valores numéricos
dados_estados['data'] = pd.to_datetime(dados_estados['data'], dayfirst=True)

# lista de datas para iterar
unique_dates = dados_estados['data'].unique()

# para pular determinados dias
start_day = 0
for i, day in enumerate(unique_dates[start_day:]):
    # seleciona os primeiros (1 a 27) estados
    sample = 27
    sort_dados_estados = dados_estados.sort_values(by=['per_mil'], ascending=False)
    dados_smpl = sort_dados_estados[sort_dados_estados['data']==day].iloc[0:sample,:]
    dados_smpl_yesterday = sort_dados_estados[sort_dados_estados['data']==unique_dates[start_day+i-1]].iloc[0:sample,:]

    # monitor de taxa de crescimento
    if sum(dados_smpl_yesterday['per_mil']) == 0:
        growth_rate = 0
    else:
        growth_rate = sum(dados_smpl['per_mil'])/sum(dados_smpl_yesterday['per_mil'])
    
    resolution = 40
    if i==0:
        growth_plot = [0]*resolution
        growth_plot[-1] = growth_rate
    else:
        for k in range(resolution,1,-1):
            growth_plot[-k] = growth_plot[-k+1]
        growth_plot[-1] = growth_rate
        
    # figuras
    fig, ax = plt.subplots(nrows=1, ncols=1, constrained_layout=True)
    y_pos = np.arange(len(dados_smpl))
    ax.barh(y_pos, dados_smpl['per_mil'], 1, align='center', color=tuple(dados_smpl['color']))
    ax.set_yticks(y_pos)
    ax.set_yticklabels(dados_smpl['estado'])
    ax.invert_yaxis()  # labels read top-to-bottom
    ax.set_title('COVID-19: casos por mil habitantes', fontsize=18, va='baseline')
    xlim = max(sort_dados_estados['per_mil'])
    #xlim = 52
    ax.set_xlim(0,xlim*1.15)
    ax.set_ylim(sample,-1)
    ax.xaxis.set_major_locator(plt.MaxNLocator(4))
    ax.ticklabel_format(style='plain', axis='x')
    ax.set_yticks(range(len(dados_smpl['estado'])))
    ax.set_yticklabels(dados_smpl['estado'])
    ax.tick_params(axis='y', which='major', pad=40, labelsize=16)
    ax.tick_params(axis='x', which='major', labelsize=16)
    
    # formata strings da data
    day_str = str(day)[:10]
    print(day_str)
    t= pd.to_datetime(str(day)) 
    day_str2 = t.strftime('%d/%m/%Y')
        
    # texto
    plt.text(1.12*xlim,0.86*sample,'{}'.format(day_str2), ha='right', fontsize=28)    
    plt.text(1.12*xlim,0.92*sample,'Taxa de crescimento: {:.2f} $\%$'.format((growth_rate-1)*100), ha='right', fontsize=16)
    plt.text(1.12*xlim,0.97*sample,'por Daniel Marostica', ha='right', fontsize=16)

    # miniplot
    iax = plt.axes([0,0,1,1])
    ip = InsetPosition(ax, [0.66, 0.23, 0.3, 0.27]) #posx, posy, width, height
    iax.set_axes_locator(ip)
    iax.plot(growth_plot)
    # ajusta a escala do monitor com a média de alguns frames
    zoom = 0.25
    average = np.average([growth_plot[-z] for z in range(20,0,-1)])
    iax.set(xlim=(0,resolution-1), ylim=(average - average*zoom, average+ average*zoom))
    iax.set_xticks([])
    iax.set_yticks([])

    # valores do histograma
    for j, v in enumerate(dados_smpl['per_mil']):
        ax.text(v + v*0.025, j + .25, str(round(v, 1)), color='black', fontweight='bold', fontsize=13, va='baseline')

    # bandeiras dos estados
    def get_flag(name):
        path = "estados/{}.png".format(name.upper())
        im = plt.imread(path)
        return im
    def offset_image(coord, name, ax):
        img = get_flag(name)
        im = OffsetImage(img, zoom=0.2)
        im.image.axes = ax
        textt = TextArea("%02d"%(coord+1))
        textt.axes = ax
        ab = AnnotationBbox(im, (0, coord),  xybox=(-30., 0.), frameon=True, xycoords='data',  boxcoords="offset points", pad=0)
        text = AnnotationBbox(textt, (0, coord),  xybox=(-11., 0.), frameon=False, xycoords='data',  boxcoords="offset points", pad=0)
        ax.add_artist(text)
        ax.add_artist(ab)

    for n, c in enumerate(dados_smpl['estado']):
        offset_image(n, c, ax)
    
    # força image_size e salva
    fig.set_size_inches(6.31,6.31)
    plt.savefig('figs/{}.png'.format(day_str), dpi=110, bbox_inches='tight')
    plt.close()

# cria gif com imagemagick (delay no último frame)
program = 'convert -delay 14 -loop 0 figs/*.png -delay 700 figs/{}.png figs/covid.gif'.format(day_str)
subprocess.call(program, shell=True)
