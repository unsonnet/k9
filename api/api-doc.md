# Table of Content

- [Product API](#product-api)
  - [POST `/product`](#post-product)
  - [POST `/product/image`](#post-productimage)
  - [PATCH `/product/image/{id}`](#patch-productimageid)
  - [GET `/product/{id}`](#get-productid)
  - [PATCH `/product/{id}`](#patch-productid)
- [Report API](#report-api)
  - [GET `/report`](#get-report)
  - [POST `/report`](#post-report)
  - [GET `/report/{id}`](#get-reportid)
  - [PATCH `/report/{id}`](#patch-reportid)

<style>
.schema {
  position: relative;
  margin: 0.4rem 0;
  padding-left: 1rem;
  border-left: 2px solid rgba(127,127,127,0.35);
}
.schema .schema {
  margin: 0.3rem 0;
  margin-left: 0.6rem;
  padding-left: 0.8rem;
  border-left: 2px solid rgba(127,127,127,0.35);
}
.schema-title {
  font-weight: 600;
  margin-bottom: 0.25rem;
  opacity: 0.85;
}
.schema-items {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin: 0;
  padding: 0;
}
.item {
  margin: 0;
  padding-bottom: 0.35rem;
  border-bottom: 1px solid rgba(127,127,127,0.35);
}
.item:last-child { border-bottom: none; }
.item-head {
  display: flex;
  align-items: baseline;
  gap: 0.4rem;
}
.item-label {
  display: inline-flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 0.25rem;
}
.field { font-weight: 600; opacity: 0.9; }
.req-asterisk {
  color: #c00;
  font-weight: 700;
  margin-left: 0.15rem;
  position: relative;
  top: -0.03rem;
}
.type {
  font-family: ui-monospace, monospace;
  opacity: 0.75;
}
.desc {
  margin-top: 0.1rem;
  line-height: 1.35;
  opacity: 0.8;
}
code {
  font-family: ui-monospace, monospace;
  background: rgba(127,127,127,0.12);
  border-radius: 3px;
  padding: 0.05rem 0.25rem;
  opacity: 0.9;
}
/* HTTP badges */
.http-method, .http-status {
  display: inline-block;
  font-family: ui-monospace, monospace;
  line-height: 1;
  color: #fff;
  border-radius: 0.35em;
  padding: 0.4em 0.4em 0.2em;
  vertical-align: baseline;
  font-weight: 600;
  box-shadow: 0 1px 2px rgba(0,0,0,0.15);
  border: 1px solid rgba(0,0,0,0.15);
}
.http-method.get { background: #2b7bba; }
.http-method.post { background: #22863a; }
.http-method.put { background: #b08800; }
.http-method.patch { background: #9467bd; }
.http-method.delete { background: #d73a49; }
.http-method.options, .http-method.head { background: #6a737d; }

.http-status {
  font-size: 0.8em;
}
.http-status.info { background: #6a737d; }
.http-status.ok { background: #28a745; }
.http-status.redirect { background: #0366d6; }
.http-status.client { background: #d73a49; }
.http-status.server { background: #6f42c1; }

.badge { font-weight: 500; opacity: 0.65; }
</style>

# Product API

- [POST `/product`](#post-product)
  - [Request](#request)
  - [Response 200 OK](#response-200-ok)
  - [Response 400 Bad Request](#response-400-bad-request)
  - [Response 401 Unauthorized](#response-401-unauthorized)
  - [Response 404 Not Found](#response-404-not-found)
  - [Response 500 Internal Server Error](#response-500-internal-server-error)
- [POST `/product/image`](#post-productimage)
  - [Request](#request)
  - [Response 200 OK](#response-200-ok)
  - [Response 400 Bad Request](#response-400-bad-request)
  - [Response 401 Unauthorized](#response-401-unauthorized)
  - [Response 500 Internal Server Error](#response-500-internal-server-error)
- [PATCH `/product/image/{id}`](#patch-productimageid)
  - [Request](#request)
  - [Response 200 OK](#response-200-ok)
  - [Response 400 Bad Request](#response-400-bad-request)
  - [Response 401 Unauthorized](#response-401-unauthorized)
  - [Response 403 Forbidden](#response-403-forbidden)
  - [Response 404 Not Found](#response-404-not-found)
  - [Response 500 Internal Server Error](#response-500-internal-server-error)
- [GET `/product/{id}`](#get-productid)
  - [Request](#request)
  - [Response 200 OK](#response-200-ok)
  - [Response 401 Unauthorized](#response-401-unauthorized)
  - [Response 403 Forbidden](#response-403-forbidden)
  - [Response 404 Not Found](#response-404-not-found)
  - [Response 500 Internal Server Error](#response-500-internal-server-error)
- [PATCH `/product/{id}`](#patch-productid)
  - [Request](#request)
  - [Response 200 OK](#response-200-ok)
  - [Response 400 Bad Request](#response-400-bad-request)
  - [Response 401 Unauthorized](#response-401-unauthorized)
  - [Response 403 Forbidden](#response-403-forbidden)
  - [Response 404 Not Found](#response-404-not-found)
  - [Response 500 Internal Server Error](#response-500-internal-server-error)
- [Back to Table of Content](#table-of-content)


## <span class="http-method post">POST</span> `/product`

Creates a new product

### Request

#### Headers

<div class="schema">
  <div class="schema-items">
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">Authorization</span><span class="req-asterisk">*</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">JWT used for authentication</div>
    </div>
  </div>
</div>

#### Body (`application/json`)

<div class="schema">
  <div class="schema-items">
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">name</span><span class="req-asterisk">*</span><span class="type"><code>name</code></span>
        </div>
      </div>
      <div class="desc">Structured name fields</div>
      <div class="schema">
        <div class="schema-title"><span class="badge">name</span></div>
        <div class="schema-items">
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">brand</span><span class="type">string</span>
              </div>
            </div>
            <div class="desc">Product brand</div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">series</span><span class="type">string</span>
              </div>
            </div>
            <div class="desc">Product series</div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">model</span><span class="type">string</span>
              </div>
            </div>
            <div class="desc">Product model</div>
          </div>
        </div>
      </div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">category</span><span class="req-asterisk">*</span><span class="type">map[string→string]</span>
        </div>
      </div>
      <div class="desc">Mapping of product attributes</div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">formats</span><span class="req-asterisk">*</span><span class="type">array[<code>format</code>]</span>
        </div>
      </div>
      <div class="desc">List of available size configurations</div>
      <div class="schema">
        <div class="schema-title"><span class="badge">format</span></div>
        <div class="schema-items">
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">length</span><span class="req-asterisk">*</span><span class="type"><code>quantity</code></span>
              </div>
            </div>
            <div class="desc">Longest dimension (same <code>unit</code> as <code>width</code>)</div>
            <div class="schema">
              <div class="schema-title"><span class="badge">quantity</span></div>
              <div class="schema-items">
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">value</span><span class="req-asterisk">*</span><span class="type">number</span>
                    </div>
                  </div>
                  <div class="desc">Numeric value (dimensionless if <code>unit</code> omitted)</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">unit</span><span class="type">string</span>
                    </div>
                  </div>
                  <div class="desc">Unit symbol (e.g. <code>mm</code>, <code>in</code>, <code>$</code>)</div>
                </div>
              </div>
            </div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">width</span><span class="req-asterisk">*</span><span class="type"><code>quantity</code></span>
              </div>
            </div>
            <div class="desc">Shortest dimension (same <code>unit</code> as <code>length</code>)</div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">thickness</span><span class="type"><code>quantity</code></span>
              </div>
            </div>
            <div class="desc">Thickness dimension (<code>unit</code> required if provided)</div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">vendors</span><span class="type">array[<code>vendor</code>]</span>
              </div>
            </div>
            <div class="desc">List of vendor listings</div>
            <div class="schema">
              <div class="schema-title"><span class="badge">vendor</span></div>
              <div class="schema-items">
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">sku</span><span class="req-asterisk">*</span><span class="type">string</span>
                    </div>
                  </div>
                  <div class="desc">Vendor product SKU</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">store</span><span class="req-asterisk">*</span><span class="type">string</span>
                    </div>
                  </div>
                  <div class="desc">Vendor name</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">name</span><span class="req-asterisk">*</span><span class="type">string</span>
                    </div>
                  </div>
                  <div class="desc">Listing name</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">price</span><span class="type"><code>quantity</code></span>
                    </div>
                  </div>
                  <div class="desc">Unit price</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">discontinued</span><span class="type">boolean</span>
                    </div>
                  </div>
                  <div class="desc">Product availability</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">url</span><span class="req-asterisk">*</span><span class="type">string</span>
                    </div>
                  </div>
                  <div class="desc">Vendor product page URL</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">images</span><span class="req-asterisk">*</span><span class="type">array[string]</span>
        </div>
      </div>
      <div class="desc">List of image IDs (<code>UUID</code>)</div>
    </div>
  </div>
</div>

### Response <span class="http-status ok">200</span> OK

#### Body (`application/json`)

<div class="schema">
  <div class="schema-title"><span class="badge">product</span></div>
  <div class="schema-items">
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">id</span><span class="req-asterisk">*</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">Product ID (<code>UUID</code>)</div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">name</span><span class="req-asterisk">*</span><span class="type"><code>name</code></span>
        </div>
      </div>
      <div class="desc">Structured name fields</div>
      <div class="schema">
        <div class="schema-title"><span class="badge">name</span></div>
        <div class="schema-items">
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">brand</span><span class="type">string</span>
              </div>
            </div>
            <div class="desc">Product brand</div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">series</span><span class="type">string</span>
              </div>
            </div>
            <div class="desc">Product series</div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">model</span><span class="type">string</span>
              </div>
            </div>
            <div class="desc">Product model</div>
          </div>
        </div>
      </div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">category</span><span class="req-asterisk">*</span><span class="type">map[string→string]</span>
        </div>
      </div>
      <div class="desc">Mapping of product attributes</div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">formats</span><span class="req-asterisk">*</span><span class="type">array[<code>format</code>]</span>
        </div>
      </div>
      <div class="desc">List of available size configurations</div>
      <div class="schema">
        <div class="schema-title"><span class="badge">format</span></div>
        <div class="schema-items">
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">length</span><span class="req-asterisk">*</span><span class="type"><code>quantity</code></span>
              </div>
            </div>
            <div class="desc">Longest dimension (same <code>unit</code> as <code>width</code>)</div>
            <div class="schema">
              <div class="schema-title"><span class="badge">quantity</span></div>
              <div class="schema-items">
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">value</span><span class="req-asterisk">*</span><span class="type">number</span>
                    </div>
                  </div>
                  <div class="desc">Numeric value (dimensionless if <code>unit</code> omitted)</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">unit</span><span class="type">string</span>
                    </div>
                  </div>
                  <div class="desc">Unit symbol (e.g. <code>mm</code>, <code>in</code>, <code>$</code>)</div>
                </div>
              </div>
            </div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">width</span><span class="req-asterisk">*</span><span class="type"><code>quantity</code></span>
              </div>
            </div>
            <div class="desc">Shortest dimension (same <code>unit</code> as <code>length</code>)</div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">thickness</span><span class="type"><code>quantity</code></span>
              </div>
            </div>
            <div class="desc">Thickness dimension (<code>unit</code> required if provided)</div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">vendors</span><span class="type">array[<code>vendor</code>]</span>
              </div>
            </div>
            <div class="desc">List of vendor listings</div>
            <div class="schema">
              <div class="schema-title"><span class="badge">vendor</span></div>
              <div class="schema-items">
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">sku</span><span class="req-asterisk">*</span><span class="type">string</span>
                    </div>
                  </div>
                  <div class="desc">Vendor product SKU</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">store</span><span class="req-asterisk">*</span><span class="type">string</span>
                    </div>
                  </div>
                  <div class="desc">Vendor name</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">name</span><span class="req-asterisk">*</span><span class="type">string</span>
                    </div>
                  </div>
                  <div class="desc">Listing name</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">price</span><span class="type"><code>quantity</code></span>
                    </div>
                  </div>
                  <div class="desc">Unit price</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">discontinued</span><span class="type">boolean</span>
                    </div>
                  </div>
                  <div class="desc">Product availability</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">url</span><span class="req-asterisk">*</span><span class="type">string</span>
                    </div>
                  </div>
                  <div class="desc">Vendor product page URL</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">images</span><span class="req-asterisk">*</span><span class="type">array[<code>image</code>]</span>
        </div>
      </div>
      <div class="desc">List of product images</div>
      <div class="schema">
        <div class="schema-title"><span class="badge">image</span></div>
        <div class="schema-items">
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">id</span><span class="req-asterisk">*</span><span class="type">string</span>
              </div>
            </div>
            <div class="desc">Image ID (<code>UUID</code>)</div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">url</span><span class="req-asterisk">*</span><span class="type">string</span>
              </div>
            </div>
            <div class="desc">Presigned S3 URL for normalized PNG image</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

### Response <span class="http-status client">400</span> Bad Request

Returned when the request body is malformed (`InvalidRequest`)

### Response <span class="http-status client">401</span> Unauthorized

Returned when authentication credentials are missing or invalid (`Unauthorized`)

### Response <span class="http-status client">404</span> Not Found

Returned when one or more referenced images do not exist (`NotFound`)

### Response <span class="http-status server">500</span> Internal Server Error

Returned when an unexpected error occurs (`InternalServerError`)

[Back to Table of Content](#table-of-content)

## <span class="http-method post">POST</span> `/product/image`

Uploads a `.jpg` image and its boolean mask and homography matrix for use in products

### Request

#### Headers

<div class="schema">
  <div class="schema-items">
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">Authorization</span><span class="req-asterisk">*</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">JWT used for authentication</div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">Content-Type</span><span class="req-asterisk">*</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">Must be <code>multipart/form-data</code></div>
    </div>
  </div>
</div>

#### Body (`multipart/form-data`)

<div class="schema">
  <div class="schema-items">
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">image</span><span class="req-asterisk">*</span><span class="type">binary</span>
        </div>
      </div>
      <div class="desc">JPG image</div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">mask</span><span class="req-asterisk">*</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">Base64-encoded <code>bool</code> mask matrix</div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">hom</span><span class="req-asterisk">*</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">Base64-encoded <code>float32[3×3]</code> homography matrix</div>
    </div>
  </div>
</div>

### Response <span class="http-status ok">200</span> OK

#### Body (`application/json`)

<div class="schema">
  <div class="schema-title"><span class="badge">image</span></div>
  <div class="schema-items">
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">id</span><span class="req-asterisk">*</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">Image ID (<code>UUID</code>)</div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">url</span><span class="req-asterisk">*</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">Presigned S3 URL for normalized PNG image</div>
    </div>
  </div>
</div>

### Response <span class="http-status client">400</span> Bad Request

Returned when the image or homography data is invalid (`InvalidImageFormat`, `InvalidHomography`)

### Response <span class="http-status client">401</span> Unauthorized

Returned when authentication credentials are missing or invalid (`Unauthorized`)

### Response <span class="http-status server">500</span> Internal Server Error

Returned when an unexpected error occurs (`InternalServerError`)

[Back to Table of Content](#table-of-content)

## <span class="http-method patch">PATCH</span> `/product/image/{id}`

Updates metadata for an uploaded, post-normalized product image

### Request

#### Headers

<div class="schema">
  <div class="schema-items">
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">Authorization</span><span class="req-asterisk">*</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">JWT used for authentication</div>
    </div>
  </div>
</div>

#### Path Parameters

<div class="schema">
  <div class="schema-items">
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">id</span><span class="req-asterisk">*</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">Image ID (<code>UUID</code>)</div>
    </div>
  </div>
</div>

#### Body (`application/json`)

<div class="schema">
  <div class="schema-items">
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">mask</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">Base64-encoded <code>bool</code> mask matrix</div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">hom</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">Base64-encoded <code>float32[3×3]</code> homography matrix</div>
    </div>
  </div>
</div>

### Response <span class="http-status ok">200</span> OK

#### Body (`application/json`)

<div class="schema">
  <div class="schema-title"><span class="badge">image</span></div>
  <div class="schema-items">
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">id</span><span class="req-asterisk">*</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">Image ID (<code>UUID</code>)</div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">url</span><span class="req-asterisk">*</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">Presigned S3 URL for normalized PNG image</div>
    </div>
  </div>
</div>

### Response <span class="http-status client">400</span> Bad Request

Returned when the request body is malformed or references invalid data (`InvalidRequest`, `InvalidBooleanMask`, `InvalidHomography`)

### Response <span class="http-status client">401</span> Unauthorized

Returned when authentication credentials are missing or invalid (`Unauthorized`)

### Response <span class="http-status client">403</span> Forbidden

Returned when the user lacks permission to modify the image (`Forbidden`)

### Response <span class="http-status client">404</span> Not Found

Returned when the image does not exist (`NotFound`)

### Response <span class="http-status server">500</span> Internal Server Error

Returned when an unexpected error occurs (`InternalServerError`)

[Back to Table of Content](#table-of-content)

## <span class="http-method get">GET</span> `/product/{id}`

Retrieves detailed data for a product

### Request

#### Headers

<div class="schema">
  <div class="schema-items">
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">Authorization</span><span class="req-asterisk">*</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">JWT used for authentication</div>
    </div>
  </div>
</div>

#### Path Parameters

<div class="schema">
  <div class="schema-items">
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">id</span><span class="req-asterisk">*</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">Product ID (<code>UUID</code>)</div>
    </div>
  </div>
</div>

### Response <span class="http-status ok">200</span> OK

#### Body (`application/json`)

<div class="schema">
  <div class="schema-title"><span class="badge">product</span></div>
  <div class="schema-items">
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">id</span><span class="req-asterisk">*</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">Product ID (<code>UUID</code>)</div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">name</span><span class="req-asterisk">*</span><span class="type"><code>name</code></span>
        </div>
      </div>
      <div class="desc">Structured name fields</div>
      <div class="schema">
        <div class="schema-title"><span class="badge">name</span></div>
        <div class="schema-items">
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">brand</span><span class="type">string</span>
              </div>
            </div>
            <div class="desc">Product brand</div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">series</span><span class="type">string</span>
              </div>
            </div>
            <div class="desc">Product series</div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">model</span><span class="type">string</span>
              </div>
            </div>
            <div class="desc">Product model</div>
          </div>
        </div>
      </div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">category</span><span class="req-asterisk">*</span><span class="type">map[string→string]</span>
        </div>
      </div>
      <div class="desc">Mapping of product attributes</div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">formats</span><span class="req-asterisk">*</span><span class="type">array[<code>format</code>]</span>
        </div>
      </div>
      <div class="desc">List of available size configurations</div>
      <div class="schema">
        <div class="schema-title"><span class="badge">format</span></div>
        <div class="schema-items">
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">length</span><span class="req-asterisk">*</span><span class="type"><code>quantity</code></span>
              </div>
            </div>
            <div class="desc">Longest dimension (same <code>unit</code> as <code>width</code>)</div>
            <div class="schema">
              <div class="schema-title"><span class="badge">quantity</span></div>
              <div class="schema-items">
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">value</span><span class="req-asterisk">*</span><span class="type">number</span>
                    </div>
                  </div>
                  <div class="desc">Numeric value (dimensionless if <code>unit</code> omitted)</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">unit</span><span class="type">string</span>
                    </div>
                  </div>
                  <div class="desc">Unit symbol (e.g. <code>mm</code>, <code>in</code>, <code>$</code>)</div>
                </div>
              </div>
            </div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">width</span><span class="req-asterisk">*</span><span class="type"><code>quantity</code></span>
              </div>
            </div>
            <div class="desc">Shortest dimension (same <code>unit</code> as <code>length</code>)</div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">thickness</span><span class="type"><code>quantity</code></span>
              </div>
            </div>
            <div class="desc">Thickness dimension (<code>unit</code> required if provided)</div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">vendors</span><span class="type">array[<code>vendor</code>]</span>
              </div>
            </div>
            <div class="desc">List of vendor listings</div>
            <div class="schema">
              <div class="schema-title"><span class="badge">vendor</span></div>
              <div class="schema-items">
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">sku</span><span class="req-asterisk">*</span><span class="type">string</span>
                    </div>
                  </div>
                  <div class="desc">Vendor product SKU</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">store</span><span class="req-asterisk">*</span><span class="type">string</span>
                    </div>
                  </div>
                  <div class="desc">Vendor name</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">name</span><span class="req-asterisk">*</span><span class="type">string</span>
                    </div>
                  </div>
                  <div class="desc">Listing name</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">price</span><span class="type"><code>quantity</code></span>
                    </div>
                  </div>
                  <div class="desc">Unit price</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">discontinued</span><span class="type">boolean</span>
                    </div>
                  </div>
                  <div class="desc">Product availability</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">url</span><span class="req-asterisk">*</span><span class="type">string</span>
                    </div>
                  </div>
                  <div class="desc">Vendor product page URL</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">images</span><span class="req-asterisk">*</span><span class="type">array[<code>image</code>]</span>
        </div>
      </div>
      <div class="desc">List of product images</div>
      <div class="schema">
        <div class="schema-title"><span class="badge">image</span></div>
        <div class="schema-items">
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">id</span><span class="req-asterisk">*</span><span class="type">string</span>
              </div>
            </div>
            <div class="desc">Image ID (<code>UUID</code>)</div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">url</span><span class="req-asterisk">*</span><span class="type">string</span>
              </div>
            </div>
            <div class="desc">Presigned S3 URL for normalized PNG image</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

### Response <span class="http-status client">401</span> Unauthorized

Returned when authentication credentials are missing or invalid (`Unauthorized`)

### Response <span class="http-status client">403</span> Forbidden

Returned when the user lacks permission to access the product (`Forbidden`)

### Response <span class="http-status client">404</span> Not Found

Returned when the product does not exist (`NotFound`)

### Response <span class="http-status server">500</span> Internal Server Error

Returned when an unexpected error occurs (`InternalServerError`)

[Back to Table of Content](#table-of-content)

## <span class="http-method patch">PATCH</span> `/product/{id}`

Updates an existing product  

Only the fields provided in the request body are updated. Unspecified fields remain unchanged

### Request

#### Headers

<div class="schema">
  <div class="schema-items">
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">Authorization</span><span class="req-asterisk">*</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">JWT used for authentication</div>
    </div>
  </div>
</div>

#### Path Parameters

<div class="schema">
  <div class="schema-items">
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">id</span><span class="req-asterisk">*</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">Product ID (<code>UUID</code>)</div>
    </div>
  </div>
</div>

#### Body (`application/json`)

<div class="schema">
  <div class="schema-items">
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">name</span><span class="type"><code>nameTest</code></span>
        </div>
      </div>
      <div class="desc">Structured name fields</div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">category</span><span class="type">map[string→string or null]</span>
        </div>
      </div>
      <div class="desc">Mapping of product attributes</div>
    </div>
  </div>
</div>

### Response <span class="http-status ok">200</span> OK

#### Body (`application/json`)

<div class="schema">
  <div class="schema-title"><span class="badge">product</span></div>
  <div class="schema-items">
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">id</span><span class="req-asterisk">*</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">Product ID (<code>UUID</code>)</div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">name</span><span class="req-asterisk">*</span><span class="type"><code>name</code></span>
        </div>
      </div>
      <div class="desc">Structured name fields</div>
      <div class="schema">
        <div class="schema-title"><span class="badge">name</span></div>
        <div class="schema-items">
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">brand</span><span class="type">string</span>
              </div>
            </div>
            <div class="desc">Product brand</div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">series</span><span class="type">string</span>
              </div>
            </div>
            <div class="desc">Product series</div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">model</span><span class="type">string</span>
              </div>
            </div>
            <div class="desc">Product model</div>
          </div>
        </div>
      </div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">category</span><span class="req-asterisk">*</span><span class="type">map[string→string]</span>
        </div>
      </div>
      <div class="desc">Mapping of product attributes</div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">formats</span><span class="req-asterisk">*</span><span class="type">array[<code>format</code>]</span>
        </div>
      </div>
      <div class="desc">List of available size configurations</div>
      <div class="schema">
        <div class="schema-title"><span class="badge">format</span></div>
        <div class="schema-items">
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">length</span><span class="req-asterisk">*</span><span class="type"><code>quantity</code></span>
              </div>
            </div>
            <div class="desc">Longest dimension (same <code>unit</code> as <code>width</code>)</div>
            <div class="schema">
              <div class="schema-title"><span class="badge">quantity</span></div>
              <div class="schema-items">
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">value</span><span class="req-asterisk">*</span><span class="type">number</span>
                    </div>
                  </div>
                  <div class="desc">Numeric value (dimensionless if <code>unit</code> omitted)</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">unit</span><span class="type">string</span>
                    </div>
                  </div>
                  <div class="desc">Unit symbol (e.g. <code>mm</code>, <code>in</code>, <code>$</code>)</div>
                </div>
              </div>
            </div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">width</span><span class="req-asterisk">*</span><span class="type"><code>quantity</code></span>
              </div>
            </div>
            <div class="desc">Shortest dimension (same <code>unit</code> as <code>length</code>)</div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">thickness</span><span class="type"><code>quantity</code></span>
              </div>
            </div>
            <div class="desc">Thickness dimension (<code>unit</code> required if provided)</div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">vendors</span><span class="type">array[<code>vendor</code>]</span>
              </div>
            </div>
            <div class="desc">List of vendor listings</div>
            <div class="schema">
              <div class="schema-title"><span class="badge">vendor</span></div>
              <div class="schema-items">
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">sku</span><span class="req-asterisk">*</span><span class="type">string</span>
                    </div>
                  </div>
                  <div class="desc">Vendor product SKU</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">store</span><span class="req-asterisk">*</span><span class="type">string</span>
                    </div>
                  </div>
                  <div class="desc">Vendor name</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">name</span><span class="req-asterisk">*</span><span class="type">string</span>
                    </div>
                  </div>
                  <div class="desc">Listing name</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">price</span><span class="type"><code>quantity</code></span>
                    </div>
                  </div>
                  <div class="desc">Unit price</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">discontinued</span><span class="type">boolean</span>
                    </div>
                  </div>
                  <div class="desc">Product availability</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">url</span><span class="req-asterisk">*</span><span class="type">string</span>
                    </div>
                  </div>
                  <div class="desc">Vendor product page URL</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">images</span><span class="req-asterisk">*</span><span class="type">array[<code>image</code>]</span>
        </div>
      </div>
      <div class="desc">List of product images</div>
      <div class="schema">
        <div class="schema-title"><span class="badge">image</span></div>
        <div class="schema-items">
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">id</span><span class="req-asterisk">*</span><span class="type">string</span>
              </div>
            </div>
            <div class="desc">Image ID (<code>UUID</code>)</div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">url</span><span class="req-asterisk">*</span><span class="type">string</span>
              </div>
            </div>
            <div class="desc">Presigned S3 URL for normalized PNG image</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

### Response <span class="http-status client">400</span> Bad Request

Returned when the request body is malformed (`InvalidRequest`)

### Response <span class="http-status client">401</span> Unauthorized

Returned when authentication credentials are missing or invalid (`Unauthorized`)

### Response <span class="http-status client">403</span> Forbidden

Returned when the user lacks permission to modify the product (`Forbidden`)

### Response <span class="http-status client">404</span> Not Found

Returned when the product or referenced images do not exist (`NotFound`)

### Response <span class="http-status server">500</span> Internal Server Error

Returned when an unexpected error occurs (`InternalServerError`)

[Back to Table of Content](#table-of-content)

# Report API

- [GET `/report`](#get-report)
  - [Request](#request)
  - [Response 200 OK](#response-200-ok)
  - [Response 401 Unauthorized](#response-401-unauthorized)
  - [Response 500 Internal Server Error](#response-500-internal-server-error)
- [POST `/report`](#post-report)
  - [Request](#request)
  - [Response 200 OK](#response-200-ok)
  - [Response 400 Bad Request](#response-400-bad-request)
  - [Response 401 Unauthorized](#response-401-unauthorized)
  - [Response 404 Not Found](#response-404-not-found)
  - [Response 500 Internal Server Error](#response-500-internal-server-error)
- [GET `/report/{id}`](#get-reportid)
  - [Request](#request)
  - [Response 200 OK](#response-200-ok)
  - [Response 401 Unauthorized](#response-401-unauthorized)
  - [Response 403 Forbidden](#response-403-forbidden)
  - [Response 404 Not Found](#response-404-not-found)
  - [Response 500 Internal Server Error](#response-500-internal-server-error)
- [PATCH `/report/{id}`](#patch-reportid)
  - [Request](#request)
  - [Response 200 OK](#response-200-ok)
  - [Response 400 Bad Request](#response-400-bad-request)
  - [Response 401 Unauthorized](#response-401-unauthorized)
  - [Response 403 Forbidden](#response-403-forbidden)
  - [Response 404 Not Found](#response-404-not-found)
  - [Response 500 Internal Server Error](#response-500-internal-server-error)
- [Back to Table of Content](#table-of-content)


## <span class="http-method get">GET</span> `/report`

Retrieves a paginated list of reports accessible to the authenticated user

### Request

#### Headers

<div class="schema">
  <div class="schema-items">
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">Authorization</span><span class="req-asterisk">*</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">JWT used for authentication</div>
    </div>
  </div>
</div>

#### Query Parameters

<div class="schema">
  <div class="schema-items">
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">limit</span><span class="type">integer</span>
        </div>
      </div>
      <div class="desc">Maximum number of reports to return per page (default: <code>25</code>)</div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">nextToken</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">Base64-encoded pagination cursor</div>
    </div>
  </div>
</div>

### Response <span class="http-status ok">200</span> OK

#### Body (`application/json`)

<div class="schema">
  <div class="schema-items">
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">total</span><span class="req-asterisk">*</span><span class="type">integer</span>
        </div>
      </div>
      <div class="desc">Total number of accessible reports</div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">nextToken</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">Base64-encoded pagination cursor for the next page</div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">reports</span><span class="req-asterisk">*</span><span class="type">array[<code>reportSummary</code>]</span>
        </div>
      </div>
      <div class="desc">List of report summaries</div>
      <div class="schema">
        <div class="schema-title"><span class="badge">reportSummary</span></div>
        <div class="schema-items">
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">id</span><span class="req-asterisk">*</span><span class="type">string</span>
              </div>
            </div>
            <div class="desc">Report ID (<code>UUID</code>)</div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">author</span><span class="req-asterisk">*</span><span class="type">string</span>
              </div>
            </div>
            <div class="desc">Author's username</div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">title</span><span class="req-asterisk">*</span><span class="type">string</span>
              </div>
            </div>
            <div class="desc">Report title</div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">date</span><span class="req-asterisk">*</span><span class="type">string</span>
              </div>
            </div>
            <div class="desc">UTC timestamp when created</div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">reference</span><span class="req-asterisk">*</span><span class="type"><code>productSummary</code></span>
              </div>
            </div>
            <div class="desc">Reference product</div>
            <div class="schema">
              <div class="schema-title"><span class="badge">productSummary</span></div>
              <div class="schema-items">
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">id</span><span class="req-asterisk">*</span><span class="type">string</span>
                    </div>
                  </div>
                  <div class="desc">Product ID (<code>UUID</code>)</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">name</span><span class="req-asterisk">*</span><span class="type"><code>name</code></span>
                    </div>
                  </div>
                  <div class="desc">Structured name fields</div>
                  <div class="schema">
                    <div class="schema-title"><span class="badge">name</span></div>
                    <div class="schema-items">
                      <div class="item">
                        <div class="item-head">
                          <div class="item-label">
                            <span class="field">brand</span><span class="type">string</span>
                          </div>
                        </div>
                        <div class="desc">Product brand</div>
                      </div>
                      <div class="item">
                        <div class="item-head">
                          <div class="item-label">
                            <span class="field">series</span><span class="type">string</span>
                          </div>
                        </div>
                        <div class="desc">Product series</div>
                      </div>
                      <div class="item">
                        <div class="item-head">
                          <div class="item-label">
                            <span class="field">model</span><span class="type">string</span>
                          </div>
                        </div>
                        <div class="desc">Product model</div>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">image</span><span class="req-asterisk">*</span><span class="type"><code>image</code></span>
                    </div>
                  </div>
                  <div class="desc">First product image</div>
                  <div class="schema">
                    <div class="schema-title"><span class="badge">image</span></div>
                    <div class="schema-items">
                      <div class="item">
                        <div class="item-head">
                          <div class="item-label">
                            <span class="field">id</span><span class="req-asterisk">*</span><span class="type">string</span>
                          </div>
                        </div>
                        <div class="desc">Image ID (<code>UUID</code>)</div>
                      </div>
                      <div class="item">
                        <div class="item-head">
                          <div class="item-label">
                            <span class="field">url</span><span class="req-asterisk">*</span><span class="type">string</span>
                          </div>
                        </div>
                        <div class="desc">Presigned S3 URL for normalized PNG image</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

### Response <span class="http-status client">401</span> Unauthorized

Returned when authentication credentials are missing or invalid (`Unauthorized`)

### Response <span class="http-status server">500</span> Internal Server Error

Returned when an unexpected error occurs (`InternalServerError`)

[Back to Table of Content](#table-of-content)

## <span class="http-method post">POST</span> `/report`

Creates a new report

### Request

#### Headers

<div class="schema">
  <div class="schema-items">
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">Authorization</span><span class="req-asterisk">*</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">JWT used for authentication</div>
    </div>
  </div>
</div>

#### Body (`application/json`)

<div class="schema">
  <div class="schema-items">
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">title</span><span class="req-asterisk">*</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">Report title</div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">reference</span><span class="req-asterisk">*</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">Reference product ID (<code>UUID</code>)</div>
    </div>
  </div>
</div>

### Response <span class="http-status ok">200</span> OK

#### Body (`application/json`)

<div class="schema">
  <div class="schema-title"><span class="badge">report</span></div>
  <div class="schema-items">
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">id</span><span class="req-asterisk">*</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">Report ID (<code>UUID</code>)</div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">author</span><span class="req-asterisk">*</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">Author's username</div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">title</span><span class="req-asterisk">*</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">Report title</div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">date</span><span class="req-asterisk">*</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">UTC timestamp when created</div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">reference</span><span class="req-asterisk">*</span><span class="type"><code>product</code></span>
        </div>
      </div>
      <div class="desc">Reference product</div>
      <div class="schema">
        <div class="schema-title"><span class="badge">product</span></div>
        <div class="schema-items">
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">id</span><span class="req-asterisk">*</span><span class="type">string</span>
              </div>
            </div>
            <div class="desc">Product ID (<code>UUID</code>)</div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">name</span><span class="req-asterisk">*</span><span class="type"><code>name</code></span>
              </div>
            </div>
            <div class="desc">Structured name fields</div>
            <div class="schema">
              <div class="schema-title"><span class="badge">name</span></div>
              <div class="schema-items">
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">brand</span><span class="type">string</span>
                    </div>
                  </div>
                  <div class="desc">Product brand</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">series</span><span class="type">string</span>
                    </div>
                  </div>
                  <div class="desc">Product series</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">model</span><span class="type">string</span>
                    </div>
                  </div>
                  <div class="desc">Product model</div>
                </div>
              </div>
            </div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">category</span><span class="req-asterisk">*</span><span class="type">map[string→string]</span>
              </div>
            </div>
            <div class="desc">Mapping of product attributes</div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">formats</span><span class="req-asterisk">*</span><span class="type">array[<code>format</code>]</span>
              </div>
            </div>
            <div class="desc">List of available size configurations</div>
            <div class="schema">
              <div class="schema-title"><span class="badge">format</span></div>
              <div class="schema-items">
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">length</span><span class="req-asterisk">*</span><span class="type"><code>quantity</code></span>
                    </div>
                  </div>
                  <div class="desc">Longest dimension (same <code>unit</code> as <code>width</code>)</div>
                  <div class="schema">
                    <div class="schema-title"><span class="badge">quantity</span></div>
                    <div class="schema-items">
                      <div class="item">
                        <div class="item-head">
                          <div class="item-label">
                            <span class="field">value</span><span class="req-asterisk">*</span><span class="type">number</span>
                          </div>
                        </div>
                        <div class="desc">Numeric value (dimensionless if <code>unit</code> omitted)</div>
                      </div>
                      <div class="item">
                        <div class="item-head">
                          <div class="item-label">
                            <span class="field">unit</span><span class="type">string</span>
                          </div>
                        </div>
                        <div class="desc">Unit symbol (e.g. <code>mm</code>, <code>in</code>, <code>$</code>)</div>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">width</span><span class="req-asterisk">*</span><span class="type"><code>quantity</code></span>
                    </div>
                  </div>
                  <div class="desc">Shortest dimension (same <code>unit</code> as <code>length</code>)</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">thickness</span><span class="type"><code>quantity</code></span>
                    </div>
                  </div>
                  <div class="desc">Thickness dimension (<code>unit</code> required if provided)</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">vendors</span><span class="type">array[<code>vendor</code>]</span>
                    </div>
                  </div>
                  <div class="desc">List of vendor listings</div>
                  <div class="schema">
                    <div class="schema-title"><span class="badge">vendor</span></div>
                    <div class="schema-items">
                      <div class="item">
                        <div class="item-head">
                          <div class="item-label">
                            <span class="field">sku</span><span class="req-asterisk">*</span><span class="type">string</span>
                          </div>
                        </div>
                        <div class="desc">Vendor product SKU</div>
                      </div>
                      <div class="item">
                        <div class="item-head">
                          <div class="item-label">
                            <span class="field">store</span><span class="req-asterisk">*</span><span class="type">string</span>
                          </div>
                        </div>
                        <div class="desc">Vendor name</div>
                      </div>
                      <div class="item">
                        <div class="item-head">
                          <div class="item-label">
                            <span class="field">name</span><span class="req-asterisk">*</span><span class="type">string</span>
                          </div>
                        </div>
                        <div class="desc">Listing name</div>
                      </div>
                      <div class="item">
                        <div class="item-head">
                          <div class="item-label">
                            <span class="field">price</span><span class="type"><code>quantity</code></span>
                          </div>
                        </div>
                        <div class="desc">Unit price</div>
                      </div>
                      <div class="item">
                        <div class="item-head">
                          <div class="item-label">
                            <span class="field">discontinued</span><span class="type">boolean</span>
                          </div>
                        </div>
                        <div class="desc">Product availability</div>
                      </div>
                      <div class="item">
                        <div class="item-head">
                          <div class="item-label">
                            <span class="field">url</span><span class="req-asterisk">*</span><span class="type">string</span>
                          </div>
                        </div>
                        <div class="desc">Vendor product page URL</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">images</span><span class="req-asterisk">*</span><span class="type">array[<code>image</code>]</span>
              </div>
            </div>
            <div class="desc">List of product images</div>
            <div class="schema">
              <div class="schema-title"><span class="badge">image</span></div>
              <div class="schema-items">
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">id</span><span class="req-asterisk">*</span><span class="type">string</span>
                    </div>
                  </div>
                  <div class="desc">Image ID (<code>UUID</code>)</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">url</span><span class="req-asterisk">*</span><span class="type">string</span>
                    </div>
                  </div>
                  <div class="desc">Presigned S3 URL for normalized PNG image</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">favorites</span><span class="type">array[<code>product</code>]</span>
        </div>
      </div>
      <div class="desc">Products marked as favorites</div>
    </div>
  </div>
</div>

### Response <span class="http-status client">400</span> Bad Request

Returned when the request body is malformed (`InvalidRequest`)

### Response <span class="http-status client">401</span> Unauthorized

Returned when authentication credentials are missing or invalid (`Unauthorized`)

### Response <span class="http-status client">404</span> Not Found

Returned when referenced images do not exist (`NotFound`)

### Response <span class="http-status server">500</span> Internal Server Error

Returned when an unexpected error occurs (`InternalServerError`)

[Back to Table of Content](#table-of-content)

## <span class="http-method get">GET</span> `/report/{id}`

Retrieves detailed data for a report

### Request

#### Headers

<div class="schema">
  <div class="schema-items">
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">Authorization</span><span class="req-asterisk">*</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">JWT used for authentication</div>
    </div>
  </div>
</div>

#### Path Parameters

<div class="schema">
  <div class="schema-items">
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">id</span><span class="req-asterisk">*</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">Report ID (<code>UUID</code>)</div>
    </div>
  </div>
</div>

### Response <span class="http-status ok">200</span> OK

#### Body (`application/json`)

<div class="schema">
  <div class="schema-title"><span class="badge">report</span></div>
  <div class="schema-items">
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">id</span><span class="req-asterisk">*</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">Report ID (<code>UUID</code>)</div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">author</span><span class="req-asterisk">*</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">Author's username</div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">title</span><span class="req-asterisk">*</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">Report title</div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">date</span><span class="req-asterisk">*</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">UTC timestamp when created</div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">reference</span><span class="req-asterisk">*</span><span class="type"><code>product</code></span>
        </div>
      </div>
      <div class="desc">Reference product</div>
      <div class="schema">
        <div class="schema-title"><span class="badge">product</span></div>
        <div class="schema-items">
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">id</span><span class="req-asterisk">*</span><span class="type">string</span>
              </div>
            </div>
            <div class="desc">Product ID (<code>UUID</code>)</div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">name</span><span class="req-asterisk">*</span><span class="type"><code>name</code></span>
              </div>
            </div>
            <div class="desc">Structured name fields</div>
            <div class="schema">
              <div class="schema-title"><span class="badge">name</span></div>
              <div class="schema-items">
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">brand</span><span class="type">string</span>
                    </div>
                  </div>
                  <div class="desc">Product brand</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">series</span><span class="type">string</span>
                    </div>
                  </div>
                  <div class="desc">Product series</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">model</span><span class="type">string</span>
                    </div>
                  </div>
                  <div class="desc">Product model</div>
                </div>
              </div>
            </div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">category</span><span class="req-asterisk">*</span><span class="type">map[string→string]</span>
              </div>
            </div>
            <div class="desc">Mapping of product attributes</div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">formats</span><span class="req-asterisk">*</span><span class="type">array[<code>format</code>]</span>
              </div>
            </div>
            <div class="desc">List of available size configurations</div>
            <div class="schema">
              <div class="schema-title"><span class="badge">format</span></div>
              <div class="schema-items">
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">length</span><span class="req-asterisk">*</span><span class="type"><code>quantity</code></span>
                    </div>
                  </div>
                  <div class="desc">Longest dimension (same <code>unit</code> as <code>width</code>)</div>
                  <div class="schema">
                    <div class="schema-title"><span class="badge">quantity</span></div>
                    <div class="schema-items">
                      <div class="item">
                        <div class="item-head">
                          <div class="item-label">
                            <span class="field">value</span><span class="req-asterisk">*</span><span class="type">number</span>
                          </div>
                        </div>
                        <div class="desc">Numeric value (dimensionless if <code>unit</code> omitted)</div>
                      </div>
                      <div class="item">
                        <div class="item-head">
                          <div class="item-label">
                            <span class="field">unit</span><span class="type">string</span>
                          </div>
                        </div>
                        <div class="desc">Unit symbol (e.g. <code>mm</code>, <code>in</code>, <code>$</code>)</div>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">width</span><span class="req-asterisk">*</span><span class="type"><code>quantity</code></span>
                    </div>
                  </div>
                  <div class="desc">Shortest dimension (same <code>unit</code> as <code>length</code>)</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">thickness</span><span class="type"><code>quantity</code></span>
                    </div>
                  </div>
                  <div class="desc">Thickness dimension (<code>unit</code> required if provided)</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">vendors</span><span class="type">array[<code>vendor</code>]</span>
                    </div>
                  </div>
                  <div class="desc">List of vendor listings</div>
                  <div class="schema">
                    <div class="schema-title"><span class="badge">vendor</span></div>
                    <div class="schema-items">
                      <div class="item">
                        <div class="item-head">
                          <div class="item-label">
                            <span class="field">sku</span><span class="req-asterisk">*</span><span class="type">string</span>
                          </div>
                        </div>
                        <div class="desc">Vendor product SKU</div>
                      </div>
                      <div class="item">
                        <div class="item-head">
                          <div class="item-label">
                            <span class="field">store</span><span class="req-asterisk">*</span><span class="type">string</span>
                          </div>
                        </div>
                        <div class="desc">Vendor name</div>
                      </div>
                      <div class="item">
                        <div class="item-head">
                          <div class="item-label">
                            <span class="field">name</span><span class="req-asterisk">*</span><span class="type">string</span>
                          </div>
                        </div>
                        <div class="desc">Listing name</div>
                      </div>
                      <div class="item">
                        <div class="item-head">
                          <div class="item-label">
                            <span class="field">price</span><span class="type"><code>quantity</code></span>
                          </div>
                        </div>
                        <div class="desc">Unit price</div>
                      </div>
                      <div class="item">
                        <div class="item-head">
                          <div class="item-label">
                            <span class="field">discontinued</span><span class="type">boolean</span>
                          </div>
                        </div>
                        <div class="desc">Product availability</div>
                      </div>
                      <div class="item">
                        <div class="item-head">
                          <div class="item-label">
                            <span class="field">url</span><span class="req-asterisk">*</span><span class="type">string</span>
                          </div>
                        </div>
                        <div class="desc">Vendor product page URL</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">images</span><span class="req-asterisk">*</span><span class="type">array[<code>image</code>]</span>
              </div>
            </div>
            <div class="desc">List of product images</div>
            <div class="schema">
              <div class="schema-title"><span class="badge">image</span></div>
              <div class="schema-items">
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">id</span><span class="req-asterisk">*</span><span class="type">string</span>
                    </div>
                  </div>
                  <div class="desc">Image ID (<code>UUID</code>)</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">url</span><span class="req-asterisk">*</span><span class="type">string</span>
                    </div>
                  </div>
                  <div class="desc">Presigned S3 URL for normalized PNG image</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">favorites</span><span class="type">array[<code>product</code>]</span>
        </div>
      </div>
      <div class="desc">Products marked as favorites</div>
    </div>
  </div>
</div>

### Response <span class="http-status client">401</span> Unauthorized

Returned when authentication credentials are missing or invalid (`Unauthorized`)

### Response <span class="http-status client">403</span> Forbidden

Returned when the user lacks permission to access the report (`Forbidden`)

### Response <span class="http-status client">404</span> Not Found

Returned when the report does not exist (`NotFound`)

### Response <span class="http-status server">500</span> Internal Server Error

Returned when an unexpected error occurs (`InternalServerError`)

[Back to Table of Content](#table-of-content)

## <span class="http-method patch">PATCH</span> `/report/{id}`

Updates an existing report  
Only the fields provided in the request body are updated. Unspecified fields remain unchanged

### Request

#### Headers

<div class="schema">
  <div class="schema-items">
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">Authorization</span><span class="req-asterisk">*</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">JWT used for authentication</div>
    </div>
  </div>
</div>

#### Path Parameters

<div class="schema">
  <div class="schema-items">
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">id</span><span class="req-asterisk">*</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">Report ID (<code>UUID</code>)</div>
    </div>
  </div>
</div>

#### Body (`application/json`)

<!-- TODO -->

### Response <span class="http-status ok">200</span> OK

#### Body (`application/json`)

<div class="schema">
  <div class="schema-title"><span class="badge">report</span></div>
  <div class="schema-items">
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">id</span><span class="req-asterisk">*</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">Report ID (<code>UUID</code>)</div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">author</span><span class="req-asterisk">*</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">Author's username</div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">title</span><span class="req-asterisk">*</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">Report title</div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">date</span><span class="req-asterisk">*</span><span class="type">string</span>
        </div>
      </div>
      <div class="desc">UTC timestamp when created</div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">reference</span><span class="req-asterisk">*</span><span class="type"><code>product</code></span>
        </div>
      </div>
      <div class="desc">Reference product</div>
      <div class="schema">
        <div class="schema-title"><span class="badge">product</span></div>
        <div class="schema-items">
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">id</span><span class="req-asterisk">*</span><span class="type">string</span>
              </div>
            </div>
            <div class="desc">Product ID (<code>UUID</code>)</div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">name</span><span class="req-asterisk">*</span><span class="type"><code>name</code></span>
              </div>
            </div>
            <div class="desc">Structured name fields</div>
            <div class="schema">
              <div class="schema-title"><span class="badge">name</span></div>
              <div class="schema-items">
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">brand</span><span class="type">string</span>
                    </div>
                  </div>
                  <div class="desc">Product brand</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">series</span><span class="type">string</span>
                    </div>
                  </div>
                  <div class="desc">Product series</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">model</span><span class="type">string</span>
                    </div>
                  </div>
                  <div class="desc">Product model</div>
                </div>
              </div>
            </div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">category</span><span class="req-asterisk">*</span><span class="type">map[string→string]</span>
              </div>
            </div>
            <div class="desc">Mapping of product attributes</div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">formats</span><span class="req-asterisk">*</span><span class="type">array[<code>format</code>]</span>
              </div>
            </div>
            <div class="desc">List of available size configurations</div>
            <div class="schema">
              <div class="schema-title"><span class="badge">format</span></div>
              <div class="schema-items">
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">length</span><span class="req-asterisk">*</span><span class="type"><code>quantity</code></span>
                    </div>
                  </div>
                  <div class="desc">Longest dimension (same <code>unit</code> as <code>width</code>)</div>
                  <div class="schema">
                    <div class="schema-title"><span class="badge">quantity</span></div>
                    <div class="schema-items">
                      <div class="item">
                        <div class="item-head">
                          <div class="item-label">
                            <span class="field">value</span><span class="req-asterisk">*</span><span class="type">number</span>
                          </div>
                        </div>
                        <div class="desc">Numeric value (dimensionless if <code>unit</code> omitted)</div>
                      </div>
                      <div class="item">
                        <div class="item-head">
                          <div class="item-label">
                            <span class="field">unit</span><span class="type">string</span>
                          </div>
                        </div>
                        <div class="desc">Unit symbol (e.g. <code>mm</code>, <code>in</code>, <code>$</code>)</div>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">width</span><span class="req-asterisk">*</span><span class="type"><code>quantity</code></span>
                    </div>
                  </div>
                  <div class="desc">Shortest dimension (same <code>unit</code> as <code>length</code>)</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">thickness</span><span class="type"><code>quantity</code></span>
                    </div>
                  </div>
                  <div class="desc">Thickness dimension (<code>unit</code> required if provided)</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">vendors</span><span class="type">array[<code>vendor</code>]</span>
                    </div>
                  </div>
                  <div class="desc">List of vendor listings</div>
                  <div class="schema">
                    <div class="schema-title"><span class="badge">vendor</span></div>
                    <div class="schema-items">
                      <div class="item">
                        <div class="item-head">
                          <div class="item-label">
                            <span class="field">sku</span><span class="req-asterisk">*</span><span class="type">string</span>
                          </div>
                        </div>
                        <div class="desc">Vendor product SKU</div>
                      </div>
                      <div class="item">
                        <div class="item-head">
                          <div class="item-label">
                            <span class="field">store</span><span class="req-asterisk">*</span><span class="type">string</span>
                          </div>
                        </div>
                        <div class="desc">Vendor name</div>
                      </div>
                      <div class="item">
                        <div class="item-head">
                          <div class="item-label">
                            <span class="field">name</span><span class="req-asterisk">*</span><span class="type">string</span>
                          </div>
                        </div>
                        <div class="desc">Listing name</div>
                      </div>
                      <div class="item">
                        <div class="item-head">
                          <div class="item-label">
                            <span class="field">price</span><span class="type"><code>quantity</code></span>
                          </div>
                        </div>
                        <div class="desc">Unit price</div>
                      </div>
                      <div class="item">
                        <div class="item-head">
                          <div class="item-label">
                            <span class="field">discontinued</span><span class="type">boolean</span>
                          </div>
                        </div>
                        <div class="desc">Product availability</div>
                      </div>
                      <div class="item">
                        <div class="item-head">
                          <div class="item-label">
                            <span class="field">url</span><span class="req-asterisk">*</span><span class="type">string</span>
                          </div>
                        </div>
                        <div class="desc">Vendor product page URL</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="item">
            <div class="item-head">
              <div class="item-label">
                <span class="field">images</span><span class="req-asterisk">*</span><span class="type">array[<code>image</code>]</span>
              </div>
            </div>
            <div class="desc">List of product images</div>
            <div class="schema">
              <div class="schema-title"><span class="badge">image</span></div>
              <div class="schema-items">
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">id</span><span class="req-asterisk">*</span><span class="type">string</span>
                    </div>
                  </div>
                  <div class="desc">Image ID (<code>UUID</code>)</div>
                </div>
                <div class="item">
                  <div class="item-head">
                    <div class="item-label">
                      <span class="field">url</span><span class="req-asterisk">*</span><span class="type">string</span>
                    </div>
                  </div>
                  <div class="desc">Presigned S3 URL for normalized PNG image</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="item">
      <div class="item-head">
        <div class="item-label">
          <span class="field">favorites</span><span class="type">array[<code>product</code>]</span>
        </div>
      </div>
      <div class="desc">Products marked as favorites</div>
    </div>
  </div>
</div>

### Response <span class="http-status client">400</span> Bad Request

Returned when the request body is malformed (`InvalidRequest`)

### Response <span class="http-status client">401</span> Unauthorized

Returned when authentication credentials are missing or invalid (`Unauthorized`)

### Response <span class="http-status client">403</span> Forbidden

Returned when the user lacks permission to modify the report (`Forbidden`)

### Response <span class="http-status client">404</span> Not Found

Returned when the report or referenced images do not exist (`NotFound`)

### Response <span class="http-status server">500</span> Internal Server Error

Returned when an unexpected error occurs (`InternalServerError`)

[Back to Table of Content](#table-of-content)
