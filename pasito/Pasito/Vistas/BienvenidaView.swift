import SwiftUI

struct BienvenidaView: View {
    @Environment(EstadoApp.self) private var estado
    @Environment(\.dismiss) private var cerrar
    @State private var paso = 0

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            HStack(spacing: 6) {
                ForEach(0..<3) { i in
                    Capsule().fill(i <= paso ? Color.hoja : Color.secondary.opacity(0.25)).frame(width: i == paso ? 22 : 8, height: 8)
                }
            }
            .animation(.spring, value: paso)

            switch paso {
            case 0:
                pregunta("¿Qué te cuesta más?") {
                    opcion("Comer bien", "Pico entre horas o como lo primero que pillo", estado.objetivo == .comer) { estado.objetivo = .comer }
                    opcion("Moverme", "Me cuesta empezar a hacer ejercicio", estado.objetivo == .mover) { estado.objetivo = .mover }
                    opcion("Las dos cosas", "Quiero cambiar un poco de todo", estado.objetivo == .ambos) { estado.objetivo = .ambos }
                }
            case 1:
                pregunta("¿Cuánto tiempo tienes al día?") {
                    ForEach(Energia.allCases) { e in
                        let r = Catalogo.rutina(e)
                        opcion("\(r.minutos) minutos", r.descripcion, estado.energia == e) { estado.energia = e }
                    }
                }
            default:
                Spacer()
                VStack(spacing: 14) {
                    ZStack {
                        Anillo(progreso: 1, grosor: 14)
                        Text("3").font(.system(size: 44, weight: .heavy, design: .rounded))
                    }
                    .frame(width: 130, height: 130)
                    Text("Tres pasitos al día").font(.title.weight(.heavy))
                    Text("Agua, algo verde y \(Catalogo.rutina(estado.energia).minutos) minutos de moverte. Si un día no puedes, hacemos el plan más pequeño, pero no lo dejamos.")
                        .multilineTextAlignment(.center).foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity)
            }

            Spacer()
            Button {
                if paso < 2 { paso += 1 } else {
                    estado.bienvenidaHecha = true
                    cerrar()
                }
            } label: {
                Text(paso < 2 ? "Siguiente" : "Empezar").bold().frame(maxWidth: .infinity).padding(.vertical, 6)
            }
            .buttonStyle(.borderedProminent)
        }
        .padding(24)
        .background(Color.fondo)
    }

    private func pregunta<C: View>(_ titulo: String, @ViewBuilder _ opciones: () -> C) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(titulo).font(.largeTitle.weight(.heavy)).padding(.top, 20).padding(.bottom, 6)
            opciones()
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
            .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).stroke(elegida ? Color.hoja : .clear, lineWidth: 1.5))
        }
        .buttonStyle(.plain)
    }
}
