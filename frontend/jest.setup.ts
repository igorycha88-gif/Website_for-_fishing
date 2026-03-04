import '@testing-library/jest-dom';

global.fetch = jest.fn();

if (typeof global.crypto === 'undefined') {
  global.crypto = require('crypto').webcrypto;
}
