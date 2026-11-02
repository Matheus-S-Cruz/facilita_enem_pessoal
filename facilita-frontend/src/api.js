/** Chamadas ao back-end. Todo erro vira ErroApi com uma mensagem pronta para mostrar. */

export class ErroApi extends Error {
  constructor(mensagem, campos = {}) {
    super(mensagem)
    this.campos = campos
  }
}

async function buscar(caminho, parametros = {}) {
  const consulta = new URLSearchParams(parametros).toString()
  let resposta
  try {
    resposta = await fetch(`/api/${caminho}${consulta ? `?${consulta}` : ''}`)
  } catch {
    throw new ErroApi('Não foi possível falar com o servidor. Confira sua conexão e tente de novo.')
  }
  const corpo = await resposta.json().catch(() => null)
  if (!resposta.ok) {
    const mensagem = typeof corpo?.detail === 'string' ? corpo.detail : 'O servidor não conseguiu calcular agora. Tente de novo em instantes.'
    throw new ErroApi(mensagem, corpo?.campos)
  }
  return corpo
}

export const buscarMetadados = () => buscar('metadados')
export const buscarRadar = (notas) => buscar('radar', notas)
export const buscarRegional = (parametros) => buscar('modulos/regional', parametros)
export const buscarOrigem = (parametros) => buscar('modulos/origem', parametros)
