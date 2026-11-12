import SwiftUI

struct ComerView: View {
    @Environment(EstadoApp.self) private var estado
    @State private var filtro: TipoComida?
    @State private var abierta: Receta?

    var body: some View {
        let p = estado.plan
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 14) {
                    menu(p)
                    platoFacil
                    Etiqueta("Todas las recetas")
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack {
                            chip("Todo", activo: filtro == nil) { filtro = nil }
                            ForEach(TipoComida.allCases) { t in chip(t.nombre, activo: filtro == t) { filtro = t } }
                        }
                    }
                    ForEach(Recetas.todas.filter { filtro == nil || $0.tipo == filtro }) { r in
                        Button { abierta = r } label: { FilaReceta(receta: r, n: p.racion(r).total) }
                            .buttonStyle(.plain)
                    }
                    cambios
                }
                .padding(.horizontal).padding(.bottom)
            }
            .pantalla("Comer")
            .sheet(item: $abierta) { DetalleRecetaView(receta: $0) }
        }
    }

    private func menu(_ p: Plan) -> some View {
        let total = estado.nutrientesHoy(soloComidas: false)
        return VStack(alignment: .leading, spacing: 0) {
            HStack {
                Etiqueta("Tu menú de hoy")
                Spacer()
                Text("\(Int(total.kcal.rounded())) / \(Int(p.kcal)) kcal").font(.footnote).monospacedDigit().foregroundStyle(.secondary)
            }
            .padding(.bottom, 6)
            ForEach(TipoComida.allCases) { t in
                let r = estado.receta(de: t)
                let n = p.racion(r, para: t).total
                if t != .desayuno { Divider() }
                HStack(spacing: 12) {
                    Button { abierta = r } label: {
                        HStack(spacing: 12) {
                            ImagenReceta(receta: r).frame(width: 62, height: 62).clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                            VStack(alignment: .leading, spacing: 2) {
                                Text("\(t.nombre.uppercased()) · \(Int(n.kcal.rounded())) KCAL")
                                    .font(.caption2.weight(.bold)).foregroundStyle(Color.hoja)
                                Text(r.nombre).font(.subheadline.weight(.semibold)).multilineTextAlignment(.leading)
                                LineaMacros(n: n)
                            }
                        }
                    }
                    .buttonStyle(.plain)
                    Spacer(minLength: 0)
                    VStack(spacing: 8) {
                        Button { estado.alternarComida(t) } label: {
                            Image(systemName: estado.comido(t) ? "checkmark.circle.fill" : "circle")
                                .font(.title2).foregroundStyle(estado.comido(t) ? Color.hoja : .secondary)
                        }
                        .accessibilityLabel(estado.comido(t) ? "Comida registrada" : "La he comido")
                        Button("Cambiar") { estado.cambiarReceta(de: t) }
                            .font(.caption.weight(.bold)).foregroundStyle(Color.cielo)
                    }
                }
                .padding(.vertical, 10)
            }
            VStack(spacing: 10) {
                BarraMacro(nombre: "Proteínas del menú", valor: total.proteinas, objetivo: p.proteinas, color: .ciruela)
                BarraMacro(nombre: "Hidratos del menú", valor: total.hidratos, objetivo: p.hidratos, color: .trigo)
                BarraMacro(nombre: "Grasas del menú", valor: total.grasas, objetivo: p.grasas, color: .cielo)
            }
            .padding(.top, 6)
        }
        .tarjeta()
    }

    private func chip(_ texto: String, activo: Bool, accion: @escaping () -> Void) -> some View {
        Button(texto, action: accion)
            .font(.subheadline.weight(.semibold))
            .padding(.horizontal, 14).padding(.vertical, 8)
            .foregroundStyle(activo ? Color.fondo : .primary)
            .background(activo ? Color.primary : Color.tarjeta, in: Capsule())
            .overlay(Capsule().stroke(Color.linea, lineWidth: activo ? 0 : 1))
    }

    private var platoFacil: some View {
        VStack(alignment: .leading, spacing: 10) {
            Etiqueta("El plato fácil")
            HStack(spacing: 16) {
                PlatoView().frame(width: 116, height: 116)
                VStack(alignment: .leading, spacing: 8) {
                    leyenda(.hoja, "½ verdura", "o ensalada")
                    leyenda(.ciruela, "¼ proteína", "huevo, pollo, pescado, legumbre")
                    leyenda(.trigo, "¼ hidratos", "arroz, pan, patata")
                }
                .font(.footnote)
            }
        }
        .tarjeta()
    }

    private func leyenda(_ color: Color, _ titulo: String, _ texto: String) -> some View {
        HStack(alignment: .firstTextBaseline, spacing: 8) {
            RoundedRectangle(cornerRadius: 3).fill(color).frame(width: 10, height: 10)
            Text("**\(titulo)**: \(texto)")
        }
    }

    private var cambios: some View {
        VStack(alignment: .leading, spacing: 10) {
            Etiqueta("Cambios pequeños")
            ForEach(Recetas.cambios, id: \.antes) { c in
                HStack {
                    Text(c.antes).strikethrough().foregroundStyle(.secondary)
                    Spacer()
                    Image(systemName: "arrow.right").foregroundStyle(.secondary)
                    Spacer()
                    Text(c.despues).fontWeight(.semibold)
                }
                .font(.subheadline)
            }
        }
        .tarjeta()
    }
}

/// Imagen del plato (en Assets, con el mismo nombre que la receta).
struct ImagenReceta: View {
    let receta: Receta
    var body: some View {
        Color.hueco
            .overlay { Image(receta.imagen).resizable().scaledToFill() }
            .clipped()
            .accessibilityLabel(receta.nombre)
    }
}

/// Plato dividido: mitad verdura, cuarto proteína, cuarto hidratos.
struct PlatoView: View {
    var body: some View {
        ZStack {
            Circle().fill(Color.tarjeta).overlay(Circle().stroke(Color.linea, lineWidth: 2))
            Sector(desde: 90, hasta: 270).fill(Color.hoja)
            Sector(desde: 270, hasta: 360).fill(Color.ciruela)
            Sector(desde: 0, hasta: 90).fill(Color.trigo)
            Sector(desde: 90, hasta: 270).stroke(Color.tarjeta, lineWidth: 3)
            Sector(desde: 270, hasta: 360).stroke(Color.tarjeta, lineWidth: 3)
        }
    }
}

private struct Sector: Shape {
    let desde: Double
    let hasta: Double
    func path(in rect: CGRect) -> Path {
        let c = CGPoint(x: rect.midX, y: rect.midY)
        var p = Path()
        p.move(to: c)
        p.addArc(center: c, radius: min(rect.width, rect.height) / 2 - 8,
                 startAngle: .degrees(desde), endAngle: .degrees(hasta), clockwise: false)
        p.closeSubpath()
        return p
    }
}

private struct FilaReceta: View {
    let receta: Receta
    let n: Nutrientes

    var body: some View {
        HStack(spacing: 12) {
            ImagenReceta(receta: receta).frame(width: 62, height: 62).clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
            VStack(alignment: .leading, spacing: 2) {
                Text(receta.nombre).font(.subheadline.weight(.semibold)).multilineTextAlignment(.leading)
                Text("\(receta.tipo.nombre) · \(Int(n.kcal.rounded())) kcal").font(.caption).foregroundStyle(.secondary)
                LineaMacros(n: n)
            }
            Spacer(minLength: 0)
            Text("\(receta.minutos) min")
                .font(.caption.weight(.bold))
                .padding(.horizontal, 8).padding(.vertical, 4)
                .background(Color.hoja.opacity(0.15), in: RoundedRectangle(cornerRadius: 8))
                .foregroundStyle(Color.hoja)
        }
        .padding(10)
        .background(Color.tarjeta, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).stroke(Color.linea, lineWidth: 1))
    }
}

struct DetalleRecetaView: View {
    @Environment(EstadoApp.self) private var estado
    @Environment(\.dismiss) private var cerrar
    let receta: Receta

    var body: some View {
        let p = estado.plan
        let racion = p.racion(receta)
        let n = racion.total
        let enMenu = estado.receta(de: receta.tipo).id == receta.id
        let comida = enMenu && estado.comido(receta.tipo)
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                ImagenReceta(receta: receta)
                    .aspectRatio(16 / 10, contentMode: .fit)
                    .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
                Text(receta.nombre).font(.title2.weight(.heavy))
                HStack {
                    pastilla(receta.tipo.nombre)
                    pastilla("\(receta.minutos) min")
                    pastilla("\(Int(n.kcal.rounded())) kcal")
                }
                Text(receta.porQue).foregroundStyle(.secondary)

                VStack(alignment: .leading, spacing: 10) {
                    Etiqueta("Macros de tu ración")
                    BarraApilada(n: n)
                    HStack(spacing: 12) {
                        Label("Proteínas \(Int(n.proteinas.rounded())) g", systemImage: "square.fill").foregroundStyle(Color.ciruela)
                        Label("Hidratos \(Int(n.hidratos.rounded())) g", systemImage: "square.fill").foregroundStyle(Color.trigo)
                        Label("Grasas \(Int(n.grasas.rounded())) g", systemImage: "square.fill").foregroundStyle(Color.cielo)
                    }
                    .font(.caption.weight(.semibold)).labelStyle(LeyendaPequena())
                    Etiqueta("Micronutrientes · % de lo que necesitas al día").padding(.top, 6)
                    micro("Fibra", n.fibra, p.fibra, "g")
                    micro("Hierro", n.hierro, p.hierro, "mg")
                    micro("Calcio", n.calcio, p.calcio, "mg")
                    micro("Vitamina C", n.vitaminaC, p.vitaminaC, "mg")
                    micro("Potasio", n.potasio, p.potasio, "mg")
                    micro("Sodio (máx.)", n.sodio, p.sodioMax, "mg")
                }
                .tarjeta()

                HStack {
                    Etiqueta("Ingredientes · 1 ración")
                    Spacer()
                    if abs(racion.factor - 1) > 0.05 {
                        Text("ajustada ×\(racion.factor.es(2))").font(.caption).foregroundStyle(.secondary)
                    }
                }
                VStack(spacing: 0) {
                    ForEach(racion.lineas) { l in
                        HStack {
                            Text(l.nombre)
                            Spacer()
                            Text(l.texto).monospacedDigit().foregroundStyle(.secondary)
                        }
                        .padding(.vertical, 8)
                        Divider()
                    }
                }
                Etiqueta("Cómo se hace")
                ForEach(Array(receta.pasos.enumerated()), id: \.offset) { i, paso in
                    HStack(alignment: .firstTextBaseline, spacing: 10) {
                        Text("\(i + 1).").bold().monospacedDigit()
                        Text(paso)
                    }
                }
                Button {
                    estado.comer(receta)
                    cerrar()
                } label: {
                    Text(comida ? "Comida registrada ✓" : enMenu ? "La he comido" : "Ponerla en mi menú y registrarla")
                        .bold().frame(maxWidth: .infinity).padding(.vertical, 6)
                }
                .buttonStyle(.borderedProminent)
                .padding(.top, 8)
            }
            .padding(20)
        }
        .background(Color.fondo)
        .presentationDetents([.large])
        .presentationDragIndicator(.visible)
    }

    private func pastilla(_ t: String) -> some View {
        Text(t).font(.caption.weight(.bold))
            .padding(.horizontal, 8).padding(.vertical, 4)
            .background(Color.hoja.opacity(0.15), in: RoundedRectangle(cornerRadius: 8))
            .foregroundStyle(Color.hoja)
    }

    private func micro(_ nombre: String, _ valor: Double, _ objetivo: Double, _ unidad: String) -> some View {
        HStack {
            Text(nombre)
            Spacer()
            Text("\(valor.es(valor < 10 ? 1 : 0)) \(unidad)").monospacedDigit()
            Text("\(Int((valor / objetivo * 100).rounded())) %").monospacedDigit().foregroundStyle(.secondary).frame(width: 48, alignment: .trailing)
        }
        .font(.subheadline)
    }
}

/// Barra con el reparto de calorías entre proteínas, hidratos y grasas.
struct BarraApilada: View {
    let n: Nutrientes
    var body: some View {
        let kp = n.proteinas * 4, kh = n.hidratos * 4, kg = n.grasas * 9
        let t = max(kp + kh + kg, 1)
        GeometryReader { g in
            HStack(spacing: 0) {
                Color.ciruela.frame(width: g.size.width * kp / t)
                Color.trigo.frame(width: g.size.width * kh / t)
                Color.cielo.frame(width: g.size.width * kg / t)
            }
        }
        .frame(height: 12)
        .clipShape(Capsule())
    }
}

private struct LeyendaPequena: LabelStyle {
    func makeBody(configuration: Configuration) -> some View {
        HStack(spacing: 4) {
            configuration.icon.font(.system(size: 8))
            configuration.title.foregroundStyle(.primary)
        }
    }
}
