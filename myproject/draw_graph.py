import matplotlib.pyplot as plt
import numpy as np
import io 
import base64
 
def build_graph(x_coordinates, y_coordinates1,y_coordinates2,data):
    img = io.BytesIO()
    fig,ax = plt.subplots()
    bar_width = 0.35
    opacity = 0.8
    index = np.arange(len(x_coordinates))
    label_x = []
    for horario in x_coordinates:
        label_x.append(horario)

    rects1 = plt.bar(index - bar_width/2 ,y_coordinates1,bar_width,alpha=opacity, color='b', label = 'Faixa 1')
    rects2 = plt.bar(index + bar_width/2,y_coordinates2,bar_width,alpha=opacity, color='g', label = 'Faixa 2')
    plt.xticks(index , label_x)
    plt.xlabel('Horário')
    plt.ylabel('Quantitativo')
    plt.title('Quantidade de veiculos por horário - ' + data)

    #Funcao para adicionar os valores de cada barra
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate('{}'.format(height),
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom')
    autolabel(rects1)
    autolabel(rects2)
    plt.legend()
    plt.tight_layout()
    plt.savefig(img, format='png')
    img.seek(0)
    graph_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    return 'data:image/png;base64,{}'.format(graph_url)
