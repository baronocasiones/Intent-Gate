// src/router.js — in-house hash router (~30 lines, decision F1)
// No react-router dependency. Works from FastAPI static mount and file:// origins.

import { useState, useEffect } from 'react'

function getHash() {
  return window.location.hash.replace(/^#/, '') || '/'
}

/**
 * Returns [currentPath, navigate].
 * currentPath is the hash path, e.g. '/runs', '/runs/demo/confirm'.
 */
export function useHashRouter() {
  const [path, setPath] = useState(getHash)

  useEffect(() => {
    const handler = () => setPath(getHash())
    window.addEventListener('hashchange', handler)
    return () => window.removeEventListener('hashchange', handler)
  }, [])

  function navigate(to) {
    window.location.hash = to
  }

  return [path, navigate]
}

/** Match a route pattern against a path. Returns params object or null. */
export function matchRoute(pattern, path) {
  const patParts = pattern.split('/')
  const pathParts = path.split('/')
  if (patParts.length !== pathParts.length) return null
  const params = {}
  for (let i = 0; i < patParts.length; i++) {
    if (patParts[i].startsWith(':')) {
      params[patParts[i].slice(1)] = pathParts[i]
    } else if (patParts[i] !== pathParts[i]) {
      return null
    }
  }
  return params
}
