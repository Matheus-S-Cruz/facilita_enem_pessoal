import { Alert, Box, Button, HStack, SimpleGrid, Spinner, Text, Wrap } from '@chakra-ui/react'
import SchoolOutlined from '@mui/icons-material/SchoolOutlined'
import { useEffect, useState } from 'react'
import { buscarOrigem } from '../../api'
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

/** Explica o quanto a origem desloca a posição, comparando o cruzamento com o Brasil. */
function frase(dados) {
  const diferenca = dados.por_renda_e_escola.percentil - dados.brasil.percentil
  const pontos = f.nota(Math.abs(diferenca)).replace(',0', '')
  const renda = dados.renda.nome.toLowerCase()
  const escola = dados.tipo_escola.nome.toLowerCase()
  if (Math.abs(diferenca) < 0.5) {
    return `Entre quem tem renda ${renda} e estudou em escola ${escola}, sua posição é praticamente a mesma que no Brasil todo.`
  }
  return diferenca > 0
    ? `Entre quem tem renda ${renda} e estudou em escola ${escola}, sua nota rende uma posição ${pontos} pontos percentuais melhor que no Brasil todo — a concorrência nesse grupo é menor.`
    : `Entre quem tem renda ${renda} e estudou em escola ${escola}, sua posição fica ${pontos} pontos percentuais abaixo da nacional — a concorrência nesse grupo é mais forte.`
}

export default function CartaoOrigem({ modulo, perfil, resultado }) {
  const [area, setArea] = useState('MEDIA')
  const [estado, setEstado] = useState({ dados: null, erro: null })
  const nota = area === 'MEDIA' ? resultado.media_geral.nota : perfil.notas[AREAS.find((a) => a.codigo === area).id]
  const renda = perfil.campos.renda
  const tipoEscola = perfil.campos.tipo_escola

  useEffect(() => {
    let atual = true
    buscarOrigem({ area, nota, renda, tipo_escola: tipoEscola })
      .then((dados) => atual && setEstado({ dados, erro: null }))
      .catch((erro) => atual && setEstado({ dados: null, erro: erro.message }))
    return () => {
      atual = false
    }
  }, [area, nota, renda, tipoEscola])

  const { dados, erro } = estado
  const carregando = !erro && dados?.area !== area

  return (
    <Cartao titulo={modulo.titulo} subtitulo={modulo.pergunta} acao={<Icone de={SchoolOutlined} color="colorPalette.fg" />}>
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
          <SimpleGrid mt="3" columns={{ base: 2, md: 4 }} gap="3">
            <Posicao rotulo="No Brasil" dados={dados.brasil} />
            <Posicao rotulo={`Renda: ${dados.renda.nome}`} dados={dados.por_renda} />
            <Posicao rotulo={`Escola ${dados.tipo_escola.nome.toLowerCase()}`} dados={dados.por_escola} />
            <Posicao rotulo="Renda e escola juntas" dados={dados.por_renda_e_escola} destaque />
          </SimpleGrid>
          <Text mt="4" textStyle="md" color="fg">{frase(dados)}</Text>
          <Text mt="4" textStyle="xs" color="fg.muted">
            A renda é a familiar mensal declarada no questionário do INEP; o tipo de escola é o do ensino médio.
          </Text>
        </Box>
      )}
    </Cartao>
  )
}
