// Shim for canvg in jsPDF to avoid missing core-js internals in standard web bundle
export class Canvg {
  static from() { return null; }
}
export default Canvg;
