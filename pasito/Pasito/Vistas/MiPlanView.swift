import SwiftUI
import Charts

struct MiPlanView: View {
    @Environment(EstadoApp.self) private var estado
    @AppStorage("apariencia") private var apariencia: Apariencia = .sistema
    @State private var editando = false

    var body: some View {
        let p = estado.plan
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 14) {
                    Text("\(p.perfil.sexo.rawValue) · \(p.perfil.edad) años · \(Int(p.perfil.altura)) cm · \(p.peso.es()) kg")
                        .font(.subheadline.weight(.semibold)).foregroundStyle(.secondary)
                    imc(p)
                    calorias(p)
                    macros(p)
                    aprende(p)
                    aparienciaTarjeta
                    Button { editando = true } label: {
                        Text("Cambiar mis datos").bold().frame(maxWidth: .infinity).padding(.vertical, 6)
                    }
                    .buttonStyle(.bordered)
                    Text("Cálculo con la fórmula de Mifflin-St Jeor. Nunca bajamos de \(p.perfil.sexo == .hombre ? "1.500" : "1.200") kcal. Si tienes diabetes, hipertensión, estás embarazada o tomas medicación, consulta con tu médico o dietista antes de empezar.")
                        .font(.footnote).foregroundStyle(.secondary)
                }
                .padding(.horizontal).padding(.bottom)
            }
            .pantalla("Mi plan")
            .fullScreenCover(isPresented: $editando) { BienvenidaView(empezarEnDatos: true) }
        }
    }

    private var aparienciaTarjeta: some View {
        VStack(alignment: .leading, spacing: 10) {
            Etiqueta("Apariencia")
            Picker("Apariencia", selection: $apariencia) {
                ForEach(Apariencia.allCases) { a in
                    Label(a.nombre, systemImage: a.icono).tag(a)
                }
            }
            .pickerStyle(.segmented)
            Text("«Automático» sigue el modo claro u oscuro de tu iPhone.")
                .font(.footnote).foregroundStyle(.secondary)
        }
        .tarjeta()
    }

    private func imc(_ p: Plan) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Etiqueta("Índice de masa corporal")
                Spacer()
                Text(p.imc.es()).font(.headline).monospacedDigit()
            }
            EscalaIMC(actual: p.imc, objetivo: p.imcObjetivo).frame(height: 34)
            Text("Ahora: \(p.categoriaIMC). Con \(p.perfil.objetivo.es()) kg tu IMC sería \(p.imcObjetivo.es()) (marca verde). El IMC es orientativo: no distingue músculo de grasa.")
                .font(.footnote).foregroundStyle(.secondary)
        }
        .tarjeta()
    }

    private func calorias(_ p: Plan) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Etiqueta("Tus calorías")
            HStack(spacing: 8) {
                Dato(valor: "\(Int(p.gasto.rounded()))", texto: "gastas al día")
                Dato(valor: "−\(Int(p.deficit.rounded()))", texto: "déficit")
                Dato(valor: "\(Int(p.kcal))", texto: "comes al día", color: .hoja)
            }
            Text("Comiendo \(Int(p.kcal)) kcal bajarás unos **\(p.ritmo.es()) kg por semana**. Llegarías a \(p.perfil.objetivo.es()) kg hacia \(p.fechaObjetivo.formatted(.dateTime.month(.wide).year().locale(Locale(identifier: "es_ES")))). Es un ritmo lento a propósito: así no pasas hambre y no recuperas el peso. Cada vez que registras tu peso, el plan se recalcula.")
                .font(.footnote).foregroundStyle(.secondary)
        }
        .tarjeta()
    }

    private func macros(_ p: Plan) -> some View {
        let datos: [(String, Double, Color)] = [("Proteínas", p.proteinas * 4, .ciruela), ("Hidratos", p.hidratos * 4, .trigo), ("Grasas", p.grasas * 9, .cielo)]
        return VStack(alignment: .leading, spacing: 12) {
            Etiqueta("Tus macros del día")
            HStack(spacing: 16) {
                Chart(datos, id: \.0) { d in
                    SectorMark(angle: .value("kcal", d.1), innerRadius: .ratio(0.6), angularInset: 1.5)
                        .foregroundStyle(d.2)
                }
                .frame(width: 116, height: 116)
                VStack(alignment: .leading, spacing: 8) {
                    leyenda(.ciruela, "\(Int(p.proteinas)) g", "proteínas · \(pct(p.proteinas * 4, p.kcal))")
                    leyenda(.trigo, "\(Int(p.hidratos)) g", "hidratos · \(pct(p.hidratos * 4, p.kcal))")
                    leyenda(.cielo, "\(Int(p.grasas)) g", "grasas · \(pct(p.grasas * 9, p.kcal))")
                    leyenda(.hoja, "\(Int(p.fibra)) g", "fibra")
                }
                .font(.footnote)
            }
            Etiqueta("Reparto por comida")
            HStack(spacing: 6) {
                ForEach(TipoComida.allCases) { t in
                    Dato(valor: "\(Int(p.kcal(para: t).rounded()))", texto: t.nombre)
                }
            }
        }
        .tarjeta()
    }

    private func pct(_ k: Double, _ total: Double) -> String { "\(Int((k / total * 100).rounded())) %" }

    private func leyenda(_ c: Color, _ valor: String, _ texto: String) -> some View {
        HStack(spacing: 8) {
            RoundedRectangle(cornerRadius: 3).fill(c).frame(width: 10, height: 10)
            Text("**\(valor)** \(texto)")
        }
    }

    private func aprende(_ p: Plan) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Etiqueta("Entiende lo que comes")
            ForEach(Nutriente.lista(p)) { n in
                DisclosureGroup {
                    VStack(alignment: .leading, spacing: 8) {
                        ForEach(n.parrafos, id: \.self) { Text(LocalizedStringKey($0)).font(.subheadline).foregroundStyle(.secondary) }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.vertical, 8)
                } label: {
                    HStack(spacing: 10) {
                        RoundedRectangle(cornerRadius: 3).fill(n.color).frame(width: 12, height: 12)
                        Text(n.nombre).font(.body.weight(.bold)).foregroundStyle(.primary)
                        Spacer()
                        Text(n.cantidad).font(.footnote).monospacedDigit().foregroundStyle(.secondary)
                    }
                }
                .padding(.vertical, 6)
                if n.id != "micro" { Divider() }
            }
        }
        .tarjeta()
    }
}

/// Barra de colores del IMC con una marca para ahora y otra (verde) para el objetivo.
private struct EscalaIMC: View {
    let actual: Double
    let objetivo: Double
    private func x(_ v: Double, _ w: CGFloat) -> CGFloat { w * CGFloat(min(1, max(0, (v - 15) / 25))) }

    var body: some View {
        GeometryReader { g in
            let w = g.size.width
            ZStack(alignment: .topLeading) {
                HStack(spacing: 0) {
                    Color.cielo.frame(width: x(18.5, w))
                    Color.hoja.frame(width: x(25, w) - x(18.5, w))
                    Color.trigo.frame(width: x(30, w) - x(25, w))
                    Color.sol
                }
                .frame(height: 10).clipShape(Capsule())
                Capsule().fill(Color.primary).frame(width: 4, height: 20).offset(x: x(actual, w) - 2, y: -5)
                Capsule().fill(Color.hoja).frame(width: 4, height: 20).overlay(Capsule().stroke(Color.tarjeta, lineWidth: 1.5))
                    .offset(x: x(objetivo, w) - 2, y: -5)
                ForEach([18.5, 25.0, 30.0], id: \.self) { v in
                    Text(v.es(v == 18.5 ? 1 : 0)).font(.system(size: 10)).foregroundStyle(.secondary)
                        .fixedSize().position(x: x(v, w), y: 26)
                }
            }
        }
    }
}

/// Textos de «Entiende lo que comes», con las cantidades de cada persona.
struct Nutriente: Identifiable {
    let id: String
    let nombre: String
    let color: Color
    let cantidad: String
    let parrafos: [String]

    static func lista(_ p: Plan) -> [Nutriente] {
        [
            Nutriente(id: "prot", nombre: "Proteínas", color: .ciruela, cantidad: "\(Int(p.proteinas)) g/día", parrafos: [
                "**Qué hacen:** construyen y reparan músculo, piel y defensas. Son lo que más sacia por caloría.",
                "**Por qué importan al adelgazar:** si comes menos y no llegas a tu proteína, pierdes músculo en vez de grasa y te entra más hambre.",
                "**Cuánto:** \(Int(p.proteinas)) g al día, unos \(Int(p.proteinas / 4)) g en cada comida principal. 4 kcal por gramo.",
                "**Dónde:** huevo, pollo, pavo, pescado, atún, yogur griego, queso batido, legumbres, tofu.",
            ]),
            Nutriente(id: "hc", nombre: "Hidratos de carbono", color: .trigo, cantidad: "\(Int(p.hidratos)) g/día", parrafos: [
                "**Qué hacen:** son el combustible principal del cerebro y de los músculos cuando te mueves.",
                "**Los buenos:** integrales, legumbres, fruta y verdura. Llevan fibra y se absorben despacio: energía estable y menos picos de hambre.",
                "**Los de limitar:** azúcar, bollería, refrescos y harinas blancas. Suben rápido y bajan rápido.",
                "**Cuánto:** \(Int(p.hidratos)) g al día. 4 kcal por gramo.",
            ]),
            Nutriente(id: "gr", nombre: "Grasas", color: .cielo, cantidad: "\(Int(p.grasas)) g/día", parrafos: [
                "**Qué hacen:** forman hormonas, ayudan a absorber las vitaminas A, D, E y K y protegen el corazón.",
                "**Las buenas:** aceite de oliva virgen, aguacate, frutos secos y pescado azul (omega-3).",
                "**Las de limitar:** fritos, embutidos, bollería industrial y ultraprocesados.",
                "**Cuánto:** \(Int(p.grasas)) g al día, el 30 % de tus calorías. 9 kcal por gramo: más del doble que proteína o hidratos, por eso medimos el aceite.",
            ]),
            Nutriente(id: "fib", nombre: "Fibra", color: .hoja, cantidad: "\(Int(p.fibra)) g/día", parrafos: [
                "**Qué hace:** sacia, regula el intestino y ralentiza la absorción del azúcar.",
                "**Dónde:** verdura, fruta con piel, legumbres, avena y pan integral.",
                "Si subes la fibra, sube también el agua.",
            ]),
            Nutriente(id: "agua", nombre: "Agua", color: .cielo, cantidad: "\(p.litrosAgua.es()) l/día", parrafos: [
                "**Cuánto:** unos 30 ml por kilo de peso para beber: \(p.vasos) vasos de 250 ml. La comida (fruta, verdura, sopas) aporta el resto.",
                "Muchas veces la sed se confunde con hambre. Antes de picar, bebe un vaso y espera 10 minutos.",
            ]),
            Nutriente(id: "micro", nombre: "Micronutrientes", color: .sol, cantidad: "vitaminas y minerales", parrafos: [
                "No dan calorías, pero el cuerpo los necesita en pequeñas cantidades. Comiendo variado se cubren casi siempre.",
                "**Hierro (\(Int(p.hierro)) mg):** lleva el oxígeno por la sangre. Legumbres, carne, espinacas. Tómalo con vitamina C para absorberlo mejor.",
                "**Calcio (\(Int(p.calcio)) mg):** huesos y músculos. Lácteos, sardinas, almendras, brócoli.",
                "**Vitamina C (\(Int(p.vitaminaC)) mg):** defensas y piel. Kiwi, fresas, pimiento, naranja.",
                "**Potasio (3.500 mg):** músculos y tensión arterial. Plátano, patata, legumbres, verdura.",
                "**Sodio (máx. 2.000 mg):** unos 5 g de sal. Ojo con embutidos, quesos curados y precocinados.",
            ]),
        ]
    }
}
