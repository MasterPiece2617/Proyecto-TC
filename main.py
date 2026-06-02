import threading
import queue
import time
import os
from graphviz import Digraph

os.environ["PATH"] += os.pathsep + r'C:\Program Files\Graphviz\bin'

# MOTOR DE GRAFOS Y AUTÓMATAS
class Node:
    def __init__(self, data):
        self.data = data
    def __repr__(self):
        return f"Node({self.data})"

class Arc:
    def __init__(self, src, tgt, fn, output=None):
        self.src = src
        self.tgt = tgt
        self.fn = fn
        self.output = output

class Graph:
    def __init__(self):
        self.nodes = []
        self.arcs = []

    def add_node(self, node):
        if node not in self.nodes:
            self.nodes.append(node)
        return node
    
    def add_arc(self, arc):
        if arc.src in self.nodes and arc.tgt in self.nodes:
            self.arcs.append(arc)

class Automaton:
    def __init__(self):
        self.graph = Graph()
        self.initial_state = None
        self.final_states = []

    def add_state(self, state):
        return self.graph.add_node(state)

    def set_initial_state(self, state):
        self.initial_state = state

    def add_transition(self, state_i, state_f, fn, output=None):
        self.graph.add_arc(Arc(state_i, state_f, fn, output))

    def add_final_state(self, state):
        if state not in self.final_states:
            self.final_states.append(state)

# COLAS DE COMUNICACIÓN INTER-HILO
atm_to_bank_queue = queue.Queue()
bank_to_atm_queue = queue.Queue()

current_atm_state = None
current_bank_state = None
channel_msg = None
render_lock = threading.Lock()
print_lock = threading.Lock()

def safe_log(msg):
    with print_lock:
        print(msg)

# MOTOR DE RENDERIZADO
def export_unified_system(atm_aut, bank_aut, atm_st, bank_st, msg_token):
    """Genera un único archivo PNG manteniendo los autómatas estáticos en su sitio."""
    dot = Digraph(comment='Sistema Integrado ULA', engine='dot')
    dot.attr(rankdir='LR', size='15,10', splines='true')
    dot.attr(rankdir='LR', splines='true')
    dot.attr(size='16,9!', ratio='fill')
    dot.attr(imagescale='true')
    dot.attr(label=f"\n\nSISTEMA INTEGRADO CONCURRENTE (M_ATM <-> M_BANK)\n", 
             labelloc="t", fontsize="16", fontname="Arial bold")

    with dot.subgraph(name='cluster_atm') as c_atm:
        c_atm.attr(label='M_ATM (Terminal Cajero)', style='filled', color='#fdfefe', fontname="Arial bold")
        for node in atm_aut.graph.nodes:
            if node == atm_st:
                c_atm.node(f"atm_{node.data}", f"[{node.data}]", style='filled', fillcolor='#fff3cd', color='#ffc107', penwidth='3')
            elif node in atm_aut.final_states:
                c_atm.node(f"atm_{node.data}", node.data, style='filled', fillcolor='#f8d7da', color='#dc3545')
            else:
                c_atm.node(f"atm_{node.data}", node.data, style='filled', fillcolor='#e2e3e5')
        for arc in atm_aut.graph.arcs:
            c_atm.edge(f"atm_{arc.src.data}", f"atm_{arc.tgt.data}")

    with dot.subgraph(name='cluster_bank') as c_bank:
        c_bank.attr(label='M_BANK (Servidor del Banco)', style='filled', color='#f4fbf7', fontname="Arial bold")
        for node in bank_aut.graph.nodes:
            if node == bank_st:
                c_bank.node(f"bank_{node.data}", f"[{node.data}]", style='filled', fillcolor='#d1e7dd', color='#198754', penwidth='3')
            elif node in bank_aut.final_states:
                c_bank.node(f"bank_{node.data}", node.data, style='filled', fillcolor='#f8d7da', color='#dc3545')
            else:
                c_bank.node(f"bank_{node.data}", node.data, style='filled', fillcolor='#e2e3e5')
        for arc in bank_aut.graph.arcs:
            c_bank.edge(f"bank_{arc.src.data}", f"bank_{arc.tgt.data}")

    q_atm_val = f"{msg_token[0]}" if msg_token and msg_token[0] else "VACÍO"
    q_bank_val = f"{msg_token[1]}" if msg_token and msg_token[1] else "VACÍO"
    
    html_table = f'''<
        <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="6" BGCOLOR="#f8f9fa">
            <TR><TD BGCOLOR="#0d6efd" COLSPAN="2"><FONT COLOR="white"><B>STACK DE MENSAJES IPC</B></FONT></TD></TR>
            <TR><TD><B>atm_to_bank_queue:</B></TD><TD WIDTH="100">{q_atm_val}</TD></TR>
            <TR><TD><B>bank_to_atm_queue:</B></TD><TD WIDTH="100">{q_bank_val}</TD></TR>
        </TABLE>
    >'''
    dot.node("msg_stack", label=html_table, shape="none")

    dot.edge("atm_R", "msg_stack", style="invis")
    dot.edge("msg_stack", "bank_p0", style="invis")

    if msg_token:
        if msg_token[0]:
            dot.edge(f"atm_{atm_st.data}", "msg_stack", color='#0d6efd', style='dashed', constraint='false')
            dot.edge("msg_stack", f"bank_{bank_st.data}", color='#0d6efd', style='dashed', constraint='false')
        elif msg_token[1]:
            dot.edge(f"bank_{bank_st.data}", "msg_stack", color='#198754', style='dashed', constraint='false')
            dot.edge("msg_stack", f"atm_{atm_st.data}", color='#198754', style='dashed', constraint='false')

    dot.render("system_live", format='png', cleanup=True, quiet=True)

def update_visuals():
    with render_lock:
        if current_atm_state and current_bank_state:
            export_unified_system(atm, bank_automata, current_atm_state, current_bank_state, channel_msg)

# CONSTRUCCIÓN FORMAL DE M_BANK
bank_automata = Automaton()
p0 = bank_automata.add_state(Node("p0"))
p_auth = bank_automata.add_state(Node("p_AUTH"))
p_check = bank_automata.add_state(Node("p_CHECK"))
p_mut = bank_automata.add_state(Node("p_MUT"))
p_block = bank_automata.add_state(Node("p_BLOCK"))

bank_automata.set_initial_state(p0)
bank_automata.add_final_state(p0)
bank_automata.add_final_state(p_block)

bank_automata.add_transition(p0, p_auth, lambda e: e == 'req_auth')
bank_automata.add_transition(p_auth, p0, lambda e: e in ['ack_ok', 'ack_fail'])
bank_automata.add_transition(p0, p_check, lambda e: e == 'req_cash')
bank_automata.add_transition(p_check, p_mut, lambda e: e == 'ack_ok')
bank_automata.add_transition(p_mut, p0, lambda e: e == 'epsilon')
bank_automata.add_transition(p_check, p0, lambda e: e == 'ack_fail')
bank_automata.add_transition(p0, p_block, lambda e: e == 'cmd_block')

def bank_thread_worker(automaton):
    global current_bank_state, channel_msg
    current_state = automaton.initial_state
    
    current_bank_state = current_state
    update_visuals()
    
    while True:
        try:
            msg = atm_to_bank_queue.get(timeout=2)
            if msg == "SHUTDOWN":
                atm_to_bank_queue.task_done()
                break
                
            event, detail = msg 
            
            target_arc = None
            for arc in automaton.graph.arcs:
                if arc.src == current_state and arc.fn(event):
                    target_arc = arc
                    break
            
            if target_arc:
                safe_log(f"  [BANCO]: Evento externo '{event}' procesado. {current_state.data} -> {target_arc.tgt.data}")
                current_state = target_arc.tgt
                current_bank_state = current_state
                update_visuals()
                time.sleep(0.5)
                
                if current_state.data == "p_AUTH":
                    resolution = "ack_ok" if detail == 'v' else "ack_fail"
                    for arc in automaton.graph.arcs:
                        if arc.src == current_state and arc.fn(resolution):
                            safe_log(f"  [BANCO]: Autenticación resuelta: '{resolution}'. {current_state.data} -> {arc.tgt.data}")
                            current_state = arc.tgt
                            break
                    
                    current_bank_state = current_state
                    channel_msg = (None, resolution)
                    update_visuals()
                    bank_to_atm_queue.put(resolution)
                    
                elif current_state.data == "p_CHECK":
                    resolution = "ack_ok" if detail == 'o' else "ack_fail"
                    for arc in automaton.graph.arcs:
                        if arc.src == current_state and arc.fn(resolution):
                            safe_log(f"  [BANCO]: Liquidez evaluada: '{resolution}'. {current_state.data} -> {arc.tgt.data}")
                            current_state = arc.tgt
                            break
                    
                    current_bank_state = current_state
                    
                    if resolution == "ack_ok":
                        channel_msg = ('epsilon', None)
                        update_visuals()
                        time.sleep(0.5)

                        for arc in automaton.graph.arcs:
                            if arc.src == current_state and arc.fn('epsilon'):
                                safe_log(f"  [BANCO]: Transición Interna Epsilon. {current_state.data} -> {arc.tgt.data}")
                                current_state = arc.tgt
                                break
                    
                    current_bank_state = current_state
                    channel_msg = (None, resolution)
                    update_visuals()
                    bank_to_atm_queue.put(resolution)
                    
                elif current_state.data == "p_BLOCK":
                    safe_log("  [BANCO]: Registro de bloqueo consolidado en almacenamiento central seguro.")
                    channel_msg = (None, "block_confirmed")
                    update_visuals()
                    bank_to_atm_queue.put("block_confirmed")
            
            atm_to_bank_queue.task_done()
        except queue.Empty:
            continue

# CONSTRUCCIÓN FORMAL DE M_ATM
atm = Automaton()
sR, sT, sI, sV, sX1, sX2, sB, sA, sN, sE, sC = [atm.add_state(Node(n)) for n in ["R", "T", "I", "V", "X1", "X2", "B", "A", "N", "E", "C"]]

atm.set_initial_state(sR)
atm.add_final_state(sR) 
atm.add_final_state(sB)

atm.add_transition(sR, sT, lambda c: c == 'i', "SOLICITAR_LECTURA_DE_TARJETA")
atm.add_transition(sT, sI, lambda c: c == 'k', "ENVIAR_REQ_AUTH_INTENTO_1")
atm.add_transition(sT, sC, lambda c: c == 'r', "PROCESAR_SOLICITUD_DE_CANCELACION")
atm.add_transition(sI, sV, lambda c: c == 'v', "AUTENTICACION_EXITOSA")
atm.add_transition(sI, sX1, lambda c: c == 'f', "MOSTRAR_ERROR_PIN_1")
atm.add_transition(sX1, sX2, lambda c: c == 'f', "MOSTRAR_ERROR_PIN_2")
atm.add_transition(sX2, sB, lambda c: c == 'f', "ENVIAR_CMD_BLOCK_TARJETA_BLOQUEADA")
atm.add_transition(sV, sA, lambda c: c == 'o', "MOSTRAR_PANTALLA_FONDOS_OK")
atm.add_transition(sV, sN, lambda c: c == 'z', "MOSTRAR_PANTALLA_SIN_SALDO")
atm.add_transition(sV, sC, lambda c: c == 'r', "CANCELAR_SESION_ACTIVA")
atm.add_transition(sA, sE, lambda c: c == 's', "ENVIAR_REQ_CASH_AL_BANCO")
atm.add_transition(sN, sE, lambda c: c == 's', "ENVIAR_REQ_CASH_AL_BANCO")
atm.add_transition(sE, sR, lambda c: c == 'r', "RECOGER_TARJETA_Y_DESPACHAR_EFECTIVO")
atm.add_transition(sC, sR, lambda c: c == 'r', "EXPULSAR_TARJETA_DEL_LECTOR")

# BUCLE DE EJECUCIÓN
def run_simulation(input_string):
    global current_atm_state, current_bank_state, channel_msg
    current_state = atm.initial_state
    current_atm_state = current_state
    current_bank_state = bank_automata.initial_state
    
    safe_log(f"\n{'='*75}\nINICIANDO PROCESAMIENTO MULTI-HILO DE LA TRAZA: '{input_string}'\n{'='*75}")
    update_visuals()
    time.sleep(1.0)
    
    for char in input_string:
        target_arc = None
        for arc in atm.graph.arcs:
            if arc.src == current_state and arc.fn(char):
                target_arc = arc
                break
                
        if not target_arc:
            safe_log(f"\n[ATM - ERROR CRÍTICO]: Transición rota. Símbolo '{char}' inválido desde el estado {current_state.data}")
            return False
            
        safe_log(f"\n[ATM]: Procesando '{char}' | {current_state.data} -> {target_arc.tgt.data}")
        if target_arc.output:
            safe_log(f"  Acción Local: {target_arc.output}")
            
        if current_state.data == "T" and char == "k":
            pass
        elif current_state.data == "I" and char in ["v", "f"]:
            safe_log(f"  >>> [ATM]: Sincronizando canal de salida. Enviando 'req_auth' ({char}) al Banco...")
            channel_msg = ("req_auth", None)
            update_visuals()
            time.sleep(1.0)
            atm_to_bank_queue.put(("req_auth", char))
            
            response = bank_to_atm_queue.get()
            safe_log(f"  <<< [ATM]: Canal liberado. Banco confirmó procesamiento: '{response}'")
            bank_to_atm_queue.task_done()
            time.sleep(1.0)
        elif current_state.data in ["X1", "X2"] and char == "f":
            if target_arc.tgt.data == "B":
                safe_log("  >>> [ATM]: ¡ESTADO DE ALERTA ALCANZADO! Solicitando congelamiento de credenciales...")
                channel_msg = ("cmd_block", None)
                update_visuals()
                time.sleep(1.0)
                atm_to_bank_queue.put(("cmd_block", None))
                
                response = bank_to_atm_queue.get()
                safe_log(f"  <<< [ATM]: Confirmación de bloqueo asentada: '{response}'")
                bank_to_atm_queue.task_done()
                time.sleep(1.0)
        elif current_state.data == "V" and char in ["o", "z"]:
            safe_log(f"  >>> [ATM]: Sincronizando canal de salida. Enviando 'req_cash' ({char}) al Banco...")
            channel_msg = ("req_cash", None)
            update_visuals()
            time.sleep(1.0)
            atm_to_bank_queue.put(("req_cash", char))
            
            response = bank_to_atm_queue.get()
            safe_log(f"  <<< [ATM]: Canal liberado. Banco confirmó procesamiento: '{response}'")
            bank_to_atm_queue.task_done()
            time.sleep(1.0)
            
        current_state = target_arc.tgt
        current_atm_state = current_state
        channel_msg = None
        update_visuals()
        time.sleep(1.0)

    success = current_state in atm.final_states
    safe_log(f"\n{'-'*75}")
    if success:
        safe_log(f"CONVERGENCIA EXITOSA: El AFD terminó en un estado de aceptación seguro: ({current_state.data})")
    else:
        safe_log(f"CONVERGENCIA RECHAZADA: Cadena incompleta o inválida. El AFD quedó atrapado en: ({current_state.data})")
    return success

if __name__ == "__main__":
    bank_thread = threading.Thread(target=bank_thread_worker, args=(bank_automata,), daemon=True)
    bank_thread.start()
    
    # Caso 1: Flujo completo correcto
    run_simulation('ikvosr')
    
    # Caso 2: Intento de fraude reiterado (3 fallos) hasta el bloqueo terminal B
    run_simulation('ikfffr')
    
    atm_to_bank_queue.put("SHUTDOWN")
    bank_thread.join(timeout=1)