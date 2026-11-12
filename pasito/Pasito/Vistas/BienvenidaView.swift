import SwiftUI

/// Bienvenida en 4 pasos: qué cuesta más, datos, actividad y resumen del plan.
struct BienvenidaView: View {
    @Environment(EstadoApp.self) private var estado
    @Environment(\.dismiss) private var cerrar
    var empezarEnDatos = false

    @State private var paso = 0
    @State private var perfil = Perfil()
    @State private var error: String?
    @AppStorage("apariencia") private var apariencia: Apariencia = .sistema

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                HStack(spacing: 6) {
                    ForEach(0..<4) { i in
                        Capsule().fill(i <= paso ? Color.hoja : Color.linea).frame(width: i == paso ? 22 : 8, height: 8)
                    }
                }
                .animation(.spring, value: paso)
                Spacer()
                if estado.bienvenidaHecha {
                    Button("Cancelar") { cerrar() }
                }
            }

            ScrollView {
                VStack(alignment: .leading, spacing: 12) {
                    switch paso {
                    case 0: pasoMeta
                    case 1: pasoDatos
                    case 2: pasoActividad
                    default: pasoResumen
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
            }
            .scrollDismissesKeyboard(.interactively)

            Button(action: siguiente) {
                Text(paso == 2 ? "Calcular mi plan" : paso == 3 ? "Empezar" : "Siguiente")
                    .bold().frame(maxWidth: .infinity).padding(.vertical, 6)
            }
            .buttonStyle(.borderedProminent)
        }
        .padding(24)
        .background(Color.fondo)
        .preferredColorScheme(apariencia.esquema)
        .onAppear {
            if estado.bienvenidaHecha {
                perfil = estado.perfil
                perfil.peso = estado.pesoActual
            }
            if empezarEnDatos { paso = 1 }
        }
    }

    private func titulo(_ t: String) -> some View {
        Text(t).font(.largeTitle.weight(.heavy)).padding(.top, 12)
    }

    private var pasoMeta: some View {
        Group {
            titulo("¿Qué te cuesta más?")
            ForEach(Meta.allCases) { m in
                opcion(m.rawValue, m.detalle, perfil.meta == m) { perfil.meta = m }
            }
        }
    }

    private var pasoDatos: some View {
        Group {
            titulo("Tus datos")
            Text("Con ellos calculamos tus calorías y tus macros. Solo se guardan en tu teléfono.")
                .foregroundStyle(.secondary)
            Picker("Sexo", selection: $perfil.sexo) {
                ForEach(Sexo.allCases) { Text($0.rawValue).tag($0) }
            }
            .pickerStyle(.segmented)
            .padding(.vertical, 6)
            LazyVGrid(columns: [GridItem(.flexible(), spacing: 12), GridItem(.flexible())], spacing: 12) {
                campo("Edad (años)", valor: Binding(get: { Double(perfil.edad) }, set: { perfil.edad = Int($0) }), decimales: false)
                campo("Altura (cm)", valor: $perfil.altura, decimales: false)
                campo("Peso actual (kg)", valor: $perfil.peso, decimales: true)
                campo("Peso objetivo (kg)", valor: $perfil.objetivo, decimales: true)
            }
            if let error {
                Text(error).font(.subheadline.weight(.semibold)).foregroundStyle(Color.aviso)
            }
        }
    }

    private func campo(_ etiqueta: String, valor: Binding<Double>, decimales: Bool) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(etiqueta).font(.caption.weight(.bold)).foregroundStyle(.secondary)
            TextField(etiqueta, value: valor, format: .number.precision(.fractionLength(0...(decimales ? 1 : 0))))
                .keyboardType(decimales ? .decimalPad : .numberPad)
                .font(.title3.weight(.semibold))
                .padding(12)
                .background(Color.tarjeta, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
                .overlay(RoundedRectangle(cornerRadius: 14, style: .continuous).stroke(Color.linea, lineWidth: 1))
        }
    }

    private var pasoActividad: some View {
        Group {
            titulo("¿Cuánto te mueves en un día normal?")
            ForEach(Actividad.allCases) { a in
                opcion(a.nombre, a.detalle, perfil.actividad == a) { perfil.actividad = a }
            }
        }
    }

    private var pasoResumen: some View {
        let p = Plan(perfil: perfil, peso: perfil.peso)
        return Group {
            titulo("Tu plan")
            HStack(spacing: 8) {
                Dato(valor: "\(Int(p.kcal))", texto: "kcal al día")
                Dato(valor: p.ritmo.es(), texto: "kg por semana")
                Dato(valor: "\(p.semanas)", texto: "semanas")
            }
            VStack(spacing: 10) {
                BarraMacro(nombre: "Proteínas", valor: p.proteinas, objetivo: p.proteinas, color: .ciruela)
                BarraMacro(nombre: "Hidratos", valor: p.hidratos, objetivo: p.hidratos, color: .trigo)
                BarraMacro(nombre: "Grasas", valor: p.grasas, objetivo: p.grasas, color: .cielo)
            }
            .tarjeta()
            Text("Bajar \(p.faltan.es()) kg sin pasar hambre. Tu menú diario ya está ajustado a estas cifras, y cada vez que te peses lo recalculamos.")
                .foregroundStyle(.secondary)
        }
    }

    private func opcion(_ titulo: String, _ detalle: String, _ elegida: Bool, _ accion: @escaping () -> Void) -> some View {
        Button(action: accion) {
            VStack(alignment: .leading, spacing: 2) {
                Text(titulo).font(.body.weight(.semibold))
                Text(detalle).font(.subheadline).foregroundStyle(.secondary)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(16)
            .background(elegida ? Color.hoja.opacity(0.15) : Color.tarjeta, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).stroke(elegida ? Color.hoja : Color.linea, lineWidth: elegida ? 1.5 : 1))
        }
        .buttonStyle(.plain)
    }

    private func siguiente() {
        if paso == 1 {
            error = Plan.validar(perfil)
            if error != nil { return }
        }
        if paso < 3 {
            withAnimation { paso += 1 }
        } else {
            estado.guardarPerfil(perfil)
            estado.bienvenidaHecha = true
            cerrar()
        }
    }
}
