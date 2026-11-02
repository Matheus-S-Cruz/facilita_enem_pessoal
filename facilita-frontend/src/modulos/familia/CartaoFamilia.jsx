import { Alert, Box, Button, HStack, SimpleGrid, Spinner, Text, Wrap } from '@chakra-ui/react'
import FamilyRestroomOutlined from '@mui/icons-material/FamilyRestroomOutlined'
import { useEffect, useState } from 'react'
import { buscarFamilia } from '../../api'
import { AREAS } from '../../campos'
import Cartao from '../../componentes/Cartao'
import Icone from '../../componentes/Icone'
import * as f from '../../formato'

const OPCOES_AREA = [{ codigo: 'MEDIA', nome: 'Média geral' }, ...AREAS]

function Posicao({ rotulo, dados, destaque }) {
  return (
    <Box p="4" rounded="l3" bg={destaque ? 'colorPalette.subtle' : 'bg.muted'} fontVariantNumeric="tabular-nums">
      <Text textStyle="sm" color="fg.muted">{rotulo}</Text>
      <Text mt="1" textStyle="3xl" fontWeight="bold" color="fg">
        {f.percentual(dados.percentil)}
      </Text>
      <Text textStyle="xs" color="fg">
        tiveram nota menor · média {f.nota(dados.media)} · {f.pessoas(dados.participantes)} pessoas
      </Text>
    </Box>
  )
}

/** Compara o deslocamento de cada recorte em relação ao Brasil e destaca o maior. */
function frase(dados) {
  const dMae = dados.por_escolaridade_mae.percentil - dados.brasil.percentil
  const dCor = dados.por_cor_raca.percentil - dados.brasil.percentil
  const forte = Math.abs(dMae) >= Math.abs(dCor) ? { d: dMae, rotulo: `quem tem mãe com "${dados.escolaridade_mae.nome.toLowerCase()}"` } : { d: dCor, rotulo: `quem declarou cor/raça ${dados.cor_raca.nome.toLowerCase()}` }
  if (Math.abs(forte.d) < 0.5) return 'Nesses recortes, sua posição é praticamente a mesma que no Brasil todo.'
  const pontos = f.nota(Math.abs(forte.d)).replace(',0', '')
  return forte.d > 0
    ? `Entre ${forte.rotulo}, sua nota rende uma posição ${pontos} pontos percentuais melhor que no Brasil todo.`
    : `Entre ${forte.rotulo}, sua posição fica ${pontos} pontos percentuais abaixo da nacional.`
}

export default function CartaoFamilia({ modulo, perfil, resultado }) {
  const [area, setArea] = useState('MEDIA')
  const [estado, setEstado] = useState({ dados: null, erro: null })
  const nota = area === 'MEDIA' ? resultado.media_geral.nota : perfil.notas[AREAS.find((a) => a.codigo === area).id]
  const escolaridadeMae = perfil.campos.escolaridade_mae
  const corRaca = perfil.campos.cor_raca

  useEffect(() => {
    let atual = true
    buscarFamilia({ area, nota, escolaridade_mae: escolaridadeMae, cor_raca: corRaca })
      .then((dados) => atual && setEstado({ dados, erro: null }))
      .catch((erro) => atual && setEstado({ dados: null, erro: erro.message }))
    return () => {
      atual = false
    }
  }, [area, nota, escolaridadeMae, corRaca])

  const { dados, erro } = estado
  const carregando = !erro && dados?.area !== area

  return (
    <Cartao titulo={modulo.titulo} subtitulo={modulo.pergunta} acao={<Icone de={FamilyRestroomOutlined} color="colorPalette.fg" />}>
      <Wrap role="radiogroup" aria-label="Área comparada" gap="1.5" mt="-1" mb="4">
        {OPCOES_AREA.map((opcao) => {
          const marcada = area === opcao.codigo
          return (
            <Button
              key={opcao.codigo}
              role="radio"
              aria-checked={marcada}
              onClick={() => setArea(opcao.codigo)}
              size="xs"
              rounded="full"
              variant={marcada ? 'solid' : 'outline'}
            >
              {opcao.nome}
            </Button>
          )
        })}
      </Wrap>

      {erro && (
        <Alert.Root status="error">
          <Alert.Indicator />
          <Alert.Title fontWeight="normal">{erro}</Alert.Title>
        </Alert.Root>
      )}
      {!erro && !dados && (
        <HStack gap="2" textStyle="sm" color="fg.muted">
          <Spinner size="sm" />
          <Text>Calculando…</Text>
        </HStack>
      )}
      {dados && (
        <Box opacity={carregando ? 0.6 : 1} aria-busy={carregando}>
          <Text textStyle="sm" color="fg">
            Com <Text as="strong" color="fg" fontVariantNumeric="tabular-nums">{f.nota(dados.nota)} pts</Text> em{' '}
            {OPCOES_AREA.find((a) => a.codigo === dados.area).nome.toLowerCase()}, veja como cada recorte muda sua posição:
          </Text>
          <SimpleGrid mt="3" columns={{ base: 1, md: 3 }} gap="3">
            <Posicao rotulo="No Brasil" dados={dados.brasil} />
            <Posicao rotulo={`Mãe: ${dados.escolaridade_mae.nome}`} dados={dados.por_escolaridade_mae} destaque />
            <Posicao rotulo={`Cor/raça: ${dados.cor_raca.nome}`} dados={dados.por_cor_raca} destaque />
          </SimpleGrid>
          <Text mt="4" textStyle="md" color="fg">{frase(dados)}</Text>
          <Text mt="4" textStyle="xs" color="fg.muted">
            Cada recorte é comparado com o Brasil separadamente, como o INEP os registra no questionário.
          </Text>
        </Box>
      )}
    </Cartao>
  )
}
