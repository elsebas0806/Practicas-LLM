"""
Motor de reglas lógicas de LogiSmart.

P = Problema reportado
S = Evidencia suficiente
Q = Riesgo de seguridad
R = Riesgo reputacional
C = Certificación vigente
H = Horario permitido

A = P ∧ S ∧ ¬Q
E = P ∧ (R ∨ Q)
C1 = P ∧ S ∧ C
H1 = P ∧ H ∧ ¬Q
"""


def aprobar_incidente(P: bool, S: bool, Q: bool) -> bool:
    return P and S and not Q


def escalar_incidente(P: bool, R: bool, Q: bool) -> bool:
    return P and (R or Q)


def certificacion_vigente(P: bool, S: bool, C: bool) -> bool:
    return P and S and C


def horario_permitido(P: bool, H: bool, Q: bool) -> bool:
    return P and H and not Q


def evaluar_reglas(
    P: bool,
    S: bool,
    Q: bool,
    R: bool,
    C: bool = True,
    H: bool = True,
) -> dict:

    A = aprobar_incidente(P, S, Q)
    E = escalar_incidente(P, R, Q)
    C1 = certificacion_vigente(P, S, C)
    H1 = horario_permitido(P, H, Q)

    return {
        "A": A,
        "E": E,
        "C1": C1,
        "H1": H1,
        "aprobar": A,
        "escalar": E,
        "certificacion_vigente": C1,
        "horario_permitido": H1,
    }


def explicar_decision(
    P: bool,
    S: bool,
    Q: bool,
    R: bool,
    C: bool = True,
    H: bool = True,
) -> list[str]:

    A = aprobar_incidente(P, S, Q)
    E = escalar_incidente(P, R, Q)
    C1 = certificacion_vigente(P, S, C)
    H1 = horario_permitido(P, H, Q)

    return [
        f"A = P({P}) AND S({S}) AND NOT Q({not Q}) -> {A}",
        f"E = P({P}) AND (R({R}) OR Q({Q})) -> {E}",
        f"C1 = P({P}) AND S({S}) AND C({C}) -> {C1}",
        f"H1 = P({P}) AND H({H}) AND NOT Q({not Q}) -> {H1}",
    ]
