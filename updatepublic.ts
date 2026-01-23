#!/usr/bin/env node
/**
 * KanjiVG Public Release Script
 *
 * Cross-platform replacement for updatepublic.sh
 * Creates release archives of KanjiVG data
 */

import fs from 'fs/promises'
import path from 'path'
import { execaCommand } from 'execa'
import archiver from 'archiver'
import { createWriteStream, createReadStream } from 'fs'
import { pipeline } from 'stream/promises'
import { createGzip } from 'zlib'

async function main() {
  const date = new Date().toISOString().slice(0, 10).replace(/-/g, '')
  const outFileOne = `kanjivg-${date}.xml.gz`
  const outFileAll = `kanjivg-${date}-all.zip`
  const outFileMain = `kanjivg-${date}-main.zip`

  console.log('📦 Creating KanjiVG release archives...')

  // Create zip of all kanji SVG files
  console.log(`Creating ${outFileAll}...`)
  await createZipArchive(outFileAll, 'kanji/**/*.svg')

  // Create zip of main kanji SVG files (5-character filenames)
  console.log(`Creating ${outFileMain}...`)
  await createZipArchive(outFileMain, 'kanji/?????.svg')

  // Run kvg.py release
  console.log('Running kvg.py release...')
  await execaCommand('python kvg.py release', { shell: true, stdio: 'inherit' })

  // Gzip kanjivg.xml
  console.log(`Creating ${outFileOne}...`)
  await gzipFile('kanjivg.xml', outFileOne)

  console.log('✅ Release archives created successfully!')
  console.log(`  - ${outFileOne}`)
  console.log(`  - ${outFileAll}`)
  console.log(`  - ${outFileMain}`)
}

async function createZipArchive(
  outputFile: string,
  pattern: string
): Promise<void> {
  return new Promise((resolve, reject) => {
    const output = createWriteStream(outputFile)
    const archive = archiver('zip', { zlib: { level: 9 } })

    output.on('close', () => resolve())
    archive.on('error', (err) => reject(err))

    archive.pipe(output)
    archive.glob(pattern)
    archive.finalize()
  })
}

async function gzipFile(inputFile: string, outputFile: string): Promise<void> {
  const gzip = createGzip()
  const source = createReadStream(inputFile)
  const destination = createWriteStream(outputFile)
  await pipeline(source, gzip, destination)
}

main().catch((error) => {
  console.error('❌ Error:', error.message)
  process.exit(1)
})
