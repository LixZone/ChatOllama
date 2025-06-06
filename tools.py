def calcule_rendement(puissance_kw, ensoleillement_h):
    """Calcule un rendement simple basé sur la puissance et l’ensoleillement."""
    rendement = puissance_kw * ensoleillement_h * 0.75  # Rendement estimé
    return f"Le rendement estimé est de {rendement:.2f} kWh par jour."

def outil_test():
    """Exemple de fonction outil."""
    print("Outil test appelé.")
    return "Tool test appelé avec succès."