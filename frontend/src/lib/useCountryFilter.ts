'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import { useRouter, usePathname, useSearchParams } from 'next/navigation'
import {
  getCountriesList,
  getSystemsForCountry,
  type CountryListEntry,
  type CountrySystem,
} from './api'

export interface CountryFilterState {
  country: string
  setCountry: (code: string) => void
  countries: CountryListEntry[] | null
  countriesError: string | null
  countrySystems: CountrySystem[] | null
  countrySystemIds: Set<string> | null
  countrySystemsError: string | null
  selectedCountry: CountryListEntry | null
}

export function useCountryFilter(): CountryFilterState {
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const country = (searchParams.get('country') || '').toUpperCase()

  const [countries, setCountries] = useState<CountryListEntry[] | null>(null)
  const [countriesError, setCountriesError] = useState<string | null>(null)
  const [countrySystems, setCountrySystems] = useState<CountrySystem[] | null>(null)
  const [countrySystemsError, setCountrySystemsError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    getCountriesList()
      .then((list) => {
        if (!cancelled) setCountries(list)
      })
      .catch(() => {
        if (!cancelled) setCountriesError('Could not load countries')
      })
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    if (!country) {
      setCountrySystems(null)
      setCountrySystemsError(null)
      return
    }
    setCountrySystems(null)
    setCountrySystemsError(null)
    getSystemsForCountry(country)
      .then((rows) => {
        if (!cancelled) setCountrySystems(rows)
      })
      .catch(() => {
        if (!cancelled) setCountrySystemsError('Could not load systems for this country')
      })
    return () => {
      cancelled = true
    }
  }, [country])

  const setCountry = useCallback(
    (code: string) => {
      const params = new URLSearchParams(searchParams.toString())
      if (code) params.set('country', code)
      else params.delete('country')
      const qs = params.toString()
      router.push(qs ? `${pathname}?${qs}` : pathname)
    },
    [router, pathname, searchParams]
  )

  const countrySystemIds = useMemo(
    () => (countrySystems ? new Set(countrySystems.map((s) => s.id)) : null),
    [countrySystems]
  )

  const selectedCountry = useMemo(
    () => (country && countries ? countries.find((c) => c.code === country) ?? null : null),
    [country, countries]
  )

  return {
    country,
    setCountry,
    countries,
    countriesError,
    countrySystems,
    countrySystemIds,
    countrySystemsError,
    selectedCountry,
  }
}
